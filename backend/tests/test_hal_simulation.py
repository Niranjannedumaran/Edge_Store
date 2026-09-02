from backend.app.hal import hal
from backend.app.config import PowerMode, DriveState


def test_simulation_storage_crud():
    storage = hal.primary_storage
    test_rel_path = "test_crud_file.txt"
    test_data = b"EdgeStore HAL Test Data Buffer"

    # Write
    assert storage.write(test_rel_path, test_data) is True
    assert storage.exists(test_rel_path) is True

    # Read
    read_back = storage.read(test_rel_path)
    assert read_back == test_data

    # List
    file_list = storage.list()
    assert test_rel_path in file_list

    # Delete
    assert storage.delete(test_rel_path) is True
    assert storage.exists(test_rel_path) is False


def test_simulation_key_device_and_encryption():
    key_dev = hal.key_device
    encryption = hal.encryption

    # Ensure key present
    key_dev.simulate_insert(valid=True)
    assert key_dev.is_present() is True
    assert key_dev.validate() is True

    key_mat = key_dev.get_key_material()
    assert key_mat is not None

    # Unlock vault
    assert encryption.unlock(key_mat) is True
    assert encryption.is_unlocked() is True

    # Lock vault
    assert encryption.lock() is True
    assert encryption.is_unlocked() is False

    # Unlock again for further tests
    assert encryption.unlock(key_mat) is True


def test_simulation_power_provider_thresholds():
    power = hal.power

    # Normal mode
    power.set_battery_level(85)
    assert power.get_power_mode() == PowerMode.NORMAL

    # Conservation mode
    power.set_battery_level(20)
    assert power.get_power_mode() == PowerMode.CONSERVATION

    # Critical mode
    power.set_battery_level(5)
    assert power.get_power_mode() == PowerMode.CRITICAL

    # Restore to 100%
    power.set_battery_level(100)
    assert power.get_power_mode() == PowerMode.NORMAL
