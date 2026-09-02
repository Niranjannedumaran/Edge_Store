# Raspberry Pi Hardware Deployment Guide

This guide walks through deploying EdgeStore onto physical Raspberry Pi 4 hardware with dual USB 3.0 HDDs, LUKS2 encryption, and removable Key-SD physical authentication.

---

## 1. Hardware Preparation

1. **Raspberry Pi 4 Model B** (4GB or 8GB RAM).
2. **OS MicroSD Card**: Flash with Raspberry Pi OS (64-bit Lite, Debian Bookworm).
3. **Key-SD**: Formatted as FAT32 with UUID label `EDGESTORE-KEY-01`.
4. **Primary HDD (Drive A)** & **Replica HDD (Drive B)**: Connect to the USB 3.0 ports (blue ports).

---

## 2. Partitioning & Stable Device Identifiers

Use GPT partition labels rather than volatile `/dev/sda` device nodes:

```bash
# Partition Primary Drive
sudo parted /dev/sda --script mklabel gpt mkpart edgestore-primary ext4 1MiB 100%

# Partition Replica Drive
sudo parted /dev/sdb --script mklabel gpt mkpart edgestore-replica ext4 1MiB 100%

# Partition Key-SD
sudo parted /dev/sdc --script mklabel gpt mkpart primary fat32 1MiB 100%
sudo mkfs.vfat -F 32 -n "EDGESTORE-KEY" -i "EDGESTORE-KEY-01" /dev/sdc1
```

---

## 3. Key-SD Enrollment & LUKS2 Formatting

1. Generate raw 512-bit key material on the Key-SD:
```bash
sudo mount /dev/disk/by-uuid/EDGESTORE-KEY-01 /mnt/key_sd
sudo dd if=/dev/urandom of=/mnt/key_sd/vault.key bs=64 count=1
sudo chmod 400 /mnt/key_sd/vault.key
```

2. Format Primary and Replica drives with LUKS2:
```bash
sudo /opt/edgestore/linux/scripts/setup_luks.sh \
    /dev/disk/by-partlabel/edgestore-primary \
    edgestore_primary \
    /mnt/key_sd/vault.key

sudo /opt/edgestore/linux/scripts/setup_luks.sh \
    /dev/disk/by-partlabel/edgestore-replica \
    edgestore_replica \
    /mnt/key_sd/vault.key

sudo umount /mnt/key_sd
```

---

## 4. Install EdgeStore Services & Udev Rules

1. Copy systemd service definitions:
```bash
sudo cp linux/systemd/*.service /etc/systemd/system/
sudo systemctl daemon-reload
```

2. Install Udev rule for Key-SD hotplug detection:
```bash
sudo cp linux/udev/99-edgestore-keysd.rules /etc/udev/rules.d/
sudo udevadm control --reload-rules
sudo udevadm trigger
```

3. Configure `/etc/edgestore/edgestore.env`:
```ini
ENVIRONMENT_MODE=raspberry_pi
HOST=0.0.0.0
PORT=8000
DEBUG=false
DATABASE_URL=sqlite:////opt/edgestore/data/edgestore.db
LINUX_PRIMARY_DEVICE=/dev/mapper/edgestore_primary
LINUX_PRIMARY_MOUNT=/mnt/edgestore/primary
LINUX_REPLICA_DEVICE=/dev/mapper/edgestore_replica
LINUX_REPLICA_MOUNT=/mnt/edgestore/replica
LINUX_KEY_SD_DEVICE_UUID=EDGESTORE-KEY-01
```

4. Enable and start services:
```bash
sudo systemctl enable edgestore-backend.service
sudo systemctl start edgestore-backend.service
```
