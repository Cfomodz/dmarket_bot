"""Tests for SkinBase item filtering and database management."""
import pytest
from modules.skinbase import SkinBase
from config import BAD_ITEMS


class TestCheckName:
    def test_valid_name(self):
        assert SkinBase.check_name('AK-47 Redline') is True

    def test_key_filtered(self):
        assert SkinBase.check_name('CS:GO Case Key') is False

    def test_sticker_filtered(self):
        assert SkinBase.check_name('Sticker | Cloud9') is False

    def test_case_filtered(self):
        assert SkinBase.check_name('Prisma Case') is False

    def test_pin_filtered(self):
        assert SkinBase.check_name('Collectible Pin') is False

    def test_operation_filtered(self):
        assert SkinBase.check_name('Operation Breakout') is False

    def test_pass_filtered(self):
        assert SkinBase.check_name('Viewer Pass') is False

    def test_capsule_filtered(self):
        assert SkinBase.check_name('Sticker Capsule') is False

    def test_graffiti_filtered(self):
        assert SkinBase.check_name('Sealed Graffiti') is False

    def test_music_filtered(self):
        assert SkinBase.check_name('Music Kit') is False

    def test_patch_filtered(self):
        assert SkinBase.check_name('Patch | Elite') is False

    def test_case_insensitive(self):
        assert SkinBase.check_name('STICKER COLLECTION') is False

    def test_all_bad_items_filtered(self):
        for item in BAD_ITEMS:
            assert SkinBase.check_name(f'Test {item} Item') is False

    def test_no_false_positive_key_in_monkey(self):
        assert SkinBase.check_name('Monkey Business') is True

    def test_no_false_positive_pin_in_pinstripe(self):
        assert SkinBase.check_name('Emerald Pinstripe') is True

    def test_no_false_positive_kit_in_toolkit(self):
        assert SkinBase.check_name('Desert Eagle Toolkit') is True
