from core.utils import deep_merge


class TestDeepMerge:
    """Test cases for the deep_merge function."""

    def test_merge_simple_dicts(self):
        """Test merging simple dictionaries."""
        base = {"a": 1, "b": 2}
        override = {"b": 3, "c": 4}
        result = deep_merge(base, override)

        expected = {"a": 1, "b": 3, "c": 4}
        assert result == expected

    def test_merge_nested_dicts(self):
        """Test merging nested dictionaries."""
        base = {"level1": {"a": 1, "b": 2, "nested": {"x": 10, "y": 20}}}
        override = {"level1": {"b": 3, "c": 4, "nested": {"y": 30, "z": 40}}}
        result = deep_merge(base, override)

        expected = {
            "level1": {"a": 1, "b": 3, "c": 4, "nested": {"x": 10, "y": 30, "z": 40}}
        }
        assert result == expected

    def test_merge_override_non_dict_with_dict(self):
        """Test overriding non-dict values with dict values."""
        base = {"a": 1, "b": "string"}
        override = {"b": {"nested": "value"}}
        result = deep_merge(base, override)

        expected = {"a": 1, "b": {"nested": "value"}}
        assert result == expected

    def test_merge_override_dict_with_non_dict(self):
        """Test overriding dict values with non-dict values."""
        base = {"a": {"nested": "value"}}
        override = {"a": "simple_string"}
        result = deep_merge(base, override)

        expected = {"a": "simple_string"}
        assert result == expected

    def test_merge_empty_dicts(self):
        """Test merging with empty dictionaries."""
        base = {"a": 1}
        override = {}
        result = deep_merge(base, override)
        assert result == {"a": 1}

        base = {}
        override = {"b": 2}
        result = deep_merge(base, override)
        assert result == {"b": 2}

    def test_merge_modifies_base_dict(self):
        """Test that deep_merge modifies the base dictionary in place."""
        base = {"a": 1}
        override = {"b": 2}
        result = deep_merge(base, override)

        # The function should modify base in place
        assert base is result
        assert base == {"a": 1, "b": 2}
