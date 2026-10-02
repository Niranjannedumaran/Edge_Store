from sqlalchemy import text, inspect
from sqlalchemy.orm import Session, sessionmaker
from backend.app.db.database import Base, engine, SessionLocal
from backend.app.models.user import User, UserRole
from backend.app.models.role import Role, Permission, role_permissions
from backend.app.models.session import UserSession
from backend.app.models.audit import AuditEvent
from backend.app.models.share import FileShare
from backend.app.core.security import hash_password
from backend.app.config import settings
from backend.app.core.logger import logger


DEFAULT_PERMISSIONS = [
    # Files
    ("files.read", "Read Files", "files", "View file lists and metadata"),
    ("files.preview", "Preview Files", "files", "Preview file content in viewer"),
    ("files.download", "Download Files", "files", "Download files from storage vault"),
    ("files.upload", "Upload Files", "files", "Upload new files to storage vault"),
    ("files.modify", "Modify Files", "files", "Modify existing file content"),
    ("files.rename", "Rename Files", "files", "Rename files"),
    ("files.delete", "Delete Files", "files", "Delete files from storage vault"),
    ("files.move", "Move Files", "files", "Move files to other directories"),
    ("files.share", "Share Files", "files", "Generate shareable links for files"),

    # Users
    ("users.read", "View Users", "users", "View user accounts and profiles"),
    ("users.create", "Create Users", "users", "Create new user and guest accounts"),
    ("users.update", "Update Users", "users", "Modify user account details"),
    ("users.disable", "Disable Users", "users", "Deactivate or suspend user accounts"),
    ("users.delete", "Delete Users", "users", "Permanently remove user accounts"),
    ("users.reset_password", "Reset Password", "users", "Reset credentials for user accounts"),
    ("users.revoke_sessions", "Revoke Sessions", "users", "Terminate active user sessions"),

    # Roles & Permissions
    ("roles.read", "View Roles", "roles", "View roles and permission matrices"),
    ("roles.create", "Create Roles", "roles", "Create custom authorization roles"),
    ("roles.update", "Update Roles", "roles", "Modify permissions assigned to roles"),
    ("roles.delete", "Delete Roles", "roles", "Remove custom authorization roles"),
    ("roles.assign", "Assign Roles", "roles", "Assign roles to user accounts"),

    # Storage
    ("storage.read", "View Storage", "storage", "View drive status, mountpoints, and capacity"),
    ("storage.manage", "Manage Storage", "storage", "Perform format, mount, and drive provisioning"),

    # Replication
    ("replication.read", "View Replication", "replication", "View sync status and replication queues"),
    ("replication.manage", "Manage Replication", "replication", "Trigger sync and retry failed files"),
    ("replication.rebuild", "Rebuild Replica", "replication", "Initiate semi-automated replica rebuild"),

    # Security
    ("security.read", "View Security", "security", "View Key-SD status, LUKS states, and access policies"),
    ("security.manage", "Manage Security", "security", "Lock and unlock vault, manage keys and policies"),

    # Audit
    ("audit.read", "View Audit Logs", "audit", "Inspect security and system audit logs"),

    # System & Hardware & Power
    ("system.read", "View System", "system", "View telemetry, health status, and uptime"),
    ("system.manage", "Manage System", "system", "Configure system settings and maintenance"),
    ("hardware.read", "View Hardware", "hardware", "View physical board, USB, and bus telemetry"),
    ("hardware.manage", "Manage Hardware", "hardware", "Control hardware simulation and fault injection"),
    ("power.read", "View Power", "power", "Monitor battery level and power telemetry"),
    ("power.manage", "Manage Power", "power", "Configure energy policies and shutdown thresholds"),
]

DEFAULT_ROLES = [
    {
        "name": "super_admin",
        "display_name": "Super Administrator",
        "description": "Full appliance administrative control with all permissions",
        "is_system": True,
        "permissions": [p[0] for p in DEFAULT_PERMISSIONS]
    },
    {
        "name": "storage_admin",
        "display_name": "Storage Administrator",
        "description": "Manages storage volumes, replication, rebuilds, and file integrity",
        "is_system": True,
        "permissions": [
            "files.read", "files.preview", "files.download", "files.upload", "files.modify",
            "files.rename", "files.delete", "files.move", "files.share",
            "storage.read", "storage.manage",
            "replication.read", "replication.manage", "replication.rebuild",
            "audit.read", "hardware.read", "system.read", "power.read"
        ]
    },
    {
        "name": "security_admin",
        "display_name": "Security Administrator",
        "description": "Manages user accounts, roles, access policies, sessions, and security audits",
        "is_system": True,
        "permissions": [
            "users.read", "users.create", "users.update", "users.disable", "users.delete",
            "users.reset_password", "users.revoke_sessions",
            "roles.read", "roles.create", "roles.update", "roles.delete", "roles.assign",
            "security.read", "security.manage",
            "audit.read", "system.read"
        ]
    },
    {
        "name": "file_manager",
        "display_name": "File Manager",
        "description": "Authorized to manage files, upload, download, and organize data",
        "is_system": True,
        "permissions": [
            "files.read", "files.preview", "files.download", "files.upload",
            "files.modify", "files.rename", "files.delete", "files.move", "files.share"
        ]
    },
    {
        "name": "guest",
        "display_name": "Guest / Viewer",
        "description": "Read-only access to view and preview authorized files",
        "is_system": True,
        "permissions": [
            "files.read", "files.preview"
        ]
    }
]


def run_migrations(eng):
    """Safely apply schema migrations to existing SQLite tables."""
    inspector = inspect(eng)
    if "users" in inspector.get_table_names():
        columns = [c["name"] for c in inspector.get_columns("users")]
        with eng.connect() as conn:
            if "display_name" not in columns:
                logger.info("Migrating users table: adding display_name column")
                conn.execute(text("ALTER TABLE users ADD COLUMN display_name VARCHAR(128)"))
            if "role_id" not in columns:
                logger.info("Migrating users table: adding role_id column")
                conn.execute(text("ALTER TABLE users ADD COLUMN role_id INTEGER REFERENCES roles(id) ON DELETE SET NULL"))
            if "expires_at" not in columns:
                logger.info("Migrating users table: adding expires_at column")
                conn.execute(text("ALTER TABLE users ADD COLUMN expires_at DATETIME"))
            conn.commit()


def init_database(target_engine=None):
    """Create tables, run migrations, seed permissions, roles, and default users."""
    eng = target_engine or engine
    logger.info("Initializing EdgeStore database tables and RBAC structures...")
    
    # Apply schema migrations for existing tables first
    run_migrations(eng)

    # Create all new tables (roles, permissions, role_permissions, user_sessions)
    Base.metadata.create_all(bind=eng)

    SessionMaker = sessionmaker(autocommit=False, autoflush=False, bind=eng)
    db: Session = SessionMaker()
    try:
        # 1. Seed Permissions
        perm_map = {}
        for code, name, cat, desc in DEFAULT_PERMISSIONS:
            perm = db.query(Permission).filter(Permission.code == code).first()
            if not perm:
                perm = Permission(code=code, name=name, category=cat, description=desc)
                db.add(perm)
                db.flush()
            perm_map[code] = perm

        # 2. Seed Roles
        role_map = {}
        for r_spec in DEFAULT_ROLES:
            role = db.query(Role).filter(Role.name == r_spec["name"]).first()
            if not role:
                role = Role(
                    name=r_spec["name"],
                    display_name=r_spec["display_name"],
                    description=r_spec["description"],
                    is_system=r_spec["is_system"]
                )
                db.add(role)
                db.flush()
            
            # Map permissions
            assigned_perms = [perm_map[code] for code in r_spec["permissions"] if code in perm_map]
            role.permissions = assigned_perms
            db.flush()
            role_map[r_spec["name"]] = role

        db.commit()

        # 3. Seed / Migrate Default Users
        super_admin_role = role_map.get("super_admin")
        storage_admin_role = role_map.get("storage_admin")
        file_manager_role = role_map.get("file_manager")
        guest_role = role_map.get("guest")

        # Super Admin
        admin_user = db.query(User).filter(User.username == settings.INITIAL_ADMIN_USERNAME).first()
        if not admin_user:
            logger.info(f"Seeding default administrator [{settings.INITIAL_ADMIN_USERNAME}]...")
            admin_user = User(
                username=settings.INITIAL_ADMIN_USERNAME,
                display_name="System Administrator",
                email=settings.INITIAL_ADMIN_EMAIL,
                hashed_password=hash_password(settings.INITIAL_ADMIN_PASSWORD),
                role="super_admin",
                role_id=super_admin_role.id if super_admin_role else None,
                is_active=True
            )
            db.add(admin_user)
            db.commit()
            db.refresh(admin_user)

            audit = AuditEvent(
                event_type="SYSTEM_INITIALIZED",
                user_id=admin_user.id,
                username=admin_user.username,
                description="EdgeStore system database and Super Administrator account initialized",
                severity="INFO"
            )
            db.add(audit)
            db.commit()
        else:
            # Upgrade existing admin
            if admin_user.role in ("admin", "super_admin"):
                admin_user.role = "super_admin"
                if super_admin_role:
                    admin_user.role_id = super_admin_role.id
                if not admin_user.display_name:
                    admin_user.display_name = "System Administrator"
                db.commit()

        # Standard Operator (File Manager / Storage Admin)
        operator = db.query(User).filter(User.username == "operator").first()
        if not operator:
            logger.info("Seeding test operator [operator]...")
            operator = User(
                username="operator",
                display_name="Storage Operator",
                email="operator@edgestore.local",
                hashed_password=hash_password("OperatorEdgeStore2026!"),
                role="storage_admin",
                role_id=storage_admin_role.id if storage_admin_role else None,
                is_active=True
            )
            db.add(operator)
            db.commit()
        else:
            if operator.role == "user":
                operator.role = "storage_admin"
                if storage_admin_role:
                    operator.role_id = storage_admin_role.id
                if not operator.display_name:
                    operator.display_name = "Storage Operator"
                db.commit()

        # Seed test Guest account
        guest = db.query(User).filter(User.username == "guest").first()
        if not guest:
            logger.info("Seeding test guest user [guest]...")
            guest = User(
                username="guest",
                display_name="Project Reviewer (Guest)",
                email="guest@edgestore.local",
                hashed_password=hash_password("GuestEdgeStore2026!"),
                role="guest",
                role_id=guest_role.id if guest_role else None,
                is_active=True
            )
            db.add(guest)
            db.commit()

        logger.info("Database initialization and RBAC configuration completed successfully.")
    except Exception as e:
        db.rollback()
        logger.error(f"Error during database initialization: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    init_database()
