import os
import datetime
from check_ircc_updates import take_screenshot
from purge_screenshots import purge_old_screenshots as pshots

def test_screenshot_and_purge():
    # Set up test directory and files
    test_dir = "test_screenshots"
    if not os.path.exists(test_dir):
        os.makedirs(test_dir)
    for i in range(10):
        filename = f"test_screenshot_{i}.png"
        filepath = os.path.join(test_dir, filename)
        with open(filepath, "w") as f:
            f.write("test")
        timestamp = datetime.datetime.now() - datetime.timedelta(days=i)
        os.utime(filepath, (timestamp.timestamp(), timestamp.timestamp()))

    # Test take_screenshot()
    driver = None  # Replace with actual WebDriver object
    screenshot_path = take_screenshot(driver)
    assert os.path.exists(screenshot_path)

    # Test purge_old_screenshots()
    num_to_keep = 5
    pshots(test_dir, num_to_keep)
    files = os.listdir(test_dir)
    assert len(files) == num_to_keep + 1  # Account for .gitkeep file
    for i in range(num_to_keep):
        filename = f"test_screenshot_{i}.png"
        assert filename in files
    for i in range(num_to_keep, 10):
        filename = f"test_screenshot_{i}.png"
        assert filename not in files

    # Clean up test directory and files
    for filename in os.listdir(test_dir):
        filepath = os.path.join(test_dir, filename)
        os.remove(filepath)
    os.rmdir(test_dir)

if __name__ == "__main__":
    test_screenshot_and_purge()