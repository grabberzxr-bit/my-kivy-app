[app]

# (str) Title of your application
title = My Kivy App

# (str) Package name (lowercase, no spaces)
package.name = mykivyapp

# (str) Package domain (needed for android packaging)
package.domain = org.test

# (str) Source code directory where main.py lives
source.dir = .

# (list) Source files to include
source.include_exts = py,png,jpg,kv,atlas

# (str) Application versioning
version = 0.1

# (list) Application requirements
requirements = python3==3.11.1,kivy


# (str) Supported orientations
orientation = portrait

# (bool) Indicate if the application should be fullscreen or not
fullscreen = 1

# ==========================================
# Android specific configuration
# ==========================================

# (list) Permissions needed for the app
android.permissions = INTERNET

# (int) Target Android API
android.api = 34

# (int) Minimum API your APK will support
android.minapi = 21

# (str) Android NDK architecture to build for.
# arm64-v8a is the primary architecture for modern phones like the Samsung M31
android.archs = arm64-v8a, armeabi-v7a

# (bool) Copy library instead of making a symbolic link
# Crucial for building inside cloud environments like Google Colab or GitHub Actions
android.copy_libs = 1

[buildozer]

# (int) Log level (0 = error only, 1 = info, 2 = debug)
log_level = 2

# (int) Display warning if buildozer is run as root
warn_on_root = 1
