from sqlalchemy.orm import Session, sessionmaker
from backend.app.db.database import Base, engine, SessionLocal
from backend.app.models.user import User, UserRole
from backend.app.models.audit import AuditEvent
from backend.app.core.security import hash_password
from backend.app.config import settings
from backend.app.core.logger import logger


def init_database(target_engine=None):
    """Create tables and seed initial users and initial audit record."""
    eng = target_engine or engine
    logger.info("Initializing EdgeStore database tables...")
    Base.metadata.create_all(bind=eng)

    SessionMaker = sessionmaker(autocommit=False, autoflush=False, bind=eng)
    db: Session = SessionMaker()
    try:
        # Check admin
        admin_user = db.query(User).filter(User.username == settings.INITIAL_ADMIN_USERNAME).first()
        if not admin_user:
            logger.info(f"Seeding default administrator [{settings.INITIAL_ADMIN_USERNAME}]...")
            admin_user = User(
                username=settings.INITIAL_ADMIN_USERNAME,
                email=settings.INITIAL_ADMIN_EMAIL,
                hashed_password=hash_password(settings.INITIAL_ADMIN_PASSWORD),
                role=UserRole.ADMIN.value,
                is_active=True
            )
            db.add(admin_user)
            db.commit()
            db.refresh(admin_user)

            # Audit record
            audit = AuditEvent(
                event_type="SYSTEM_INITIALIZED",
                user_id=admin_user.id,
                username=admin_user.username,
                description="EdgeStore system database and admin account initialized",
                severity="INFO"
            )
            db.add(audit)
            db.commit()

        # Check standard operator user for testing RBAC
        operator = db.query(User).filter(User.username == "operator").first()
        if not operator:
            logger.info("Seeding test standard user [operator]...")
            operator = User(
                username="operator",
                email="operator@edgestore.local",
                hashed_password=hash_password("OperatorEdgeStore2026!"),
                role=UserRole.USER.value,
                is_active=True
            )
            db.add(operator)
            db.commit()

        logger.info("Database initialization completed successfully.")
    except Exception as e:
        db.rollback()
        logger.error(f"Error during database initialization: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    init_database()
