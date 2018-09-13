"""Unit tests for the kubetest.manifest package."""

import os

import pytest
import yaml
from kubernetes import client

from kubetest import manifest


class TestCastValue:
    """Tests for kubetest.manifest.cast_value"""

    @pytest.mark.parametrize(
        'value,t,expected', [
            # builtin types
            (11, 'int', int(11)),
            ('11', 'int', int(11)),
            (11.0, 'int', int(11)),
            (11, 'float', float(11)),
            (11, 'str', '11'),

            # casting to object should result in no change
            (11, 'object', 11),
            ('11', 'object', '11'),

            # kubernetes types
            (
                {'apiVersion': 'apps/v1', 'kind': 'Namespace'},
                'V1Namespace',
                client.V1Namespace(kind='Namespace', api_version='apps/v1')),
            (
                {'fieldRef': {'apiVersion': 'apps/v1beta1', 'fieldPath': 'foobar'}},
                'V1EnvVarSource',
                client.V1EnvVarSource(field_ref=client.V1ObjectFieldSelector(
                    api_version='apps/v1beta1', field_path='foobar'
                ))),
            (
                {'finalizers': ['a', 'b', 'c']},
                'V1ObjectMeta',
                client.V1ObjectMeta(finalizers=['a', 'b', 'c'])),
        ]
    )
    def test_ok(self, value, t, expected):
        """Test casting values to the specified type successfully."""

        actual = manifest.cast_value(value, t)
        assert type(actual) == type(expected)
        assert actual == expected

    @pytest.mark.parametrize(
        'value,t,error', [
            # builtin types
            ({'foo': 'bar'}, 'int', TypeError),
            ([1, 3, 5], 'float', TypeError),
            (1.0, 'set', TypeError),

            # kubernetes types
            (11, 'V1Namespace', AttributeError),
            ('foo', 'V1Deployment', AttributeError),
            (['a', 'b', 'c'], 'V1Service', AttributeError),
            ({1, 2, 3, 4}, 'V1Pod', AttributeError),

            # unknown type
            (11, 'NotARealType', ValueError),
        ]
    )
    def test_error(self, value, t, error):
        """Test casting values to the specified type unsuccessfully."""

        with pytest.raises(error):
            manifest.cast_value(value, t)


class TestNewObject:
    """Tests for kubetest.manifest.new_object"""

    # TODO - a lot of this is tested implicitly in TestLoadType. Once we have
    # test coverage set up, can add tests based on whats missing.


class TestLoadType:
    """Tests for kubetest.manifest.load_type"""

    def test_simple_deployment_ok(self, manifest_dir, simple_deployment):
        """Test loading the simple deployment successfully."""
        obj = manifest.load_type(
            client.V1Deployment,
            os.path.join(manifest_dir, 'simple-deployment.yaml')
        )
        assert obj == simple_deployment

    def test_simple_deployment_wrong_type(self, manifest_dir):
        """Test loading the simple deployment to the wrong type."""
        with pytest.raises(ValueError):
            # The V1Container requires a name -- since the manifest has no name,
            # it will cause V1Container construction to fail with ValueError.
            manifest.load_type(
                client.V1Container,
                os.path.join(manifest_dir, 'simple-deployment.yaml')
            )

    def test_simple_service_ok(self, manifest_dir, simple_service):
        """Test loading the simple service successfully."""
        obj = manifest.load_type(
            client.V1Service,
            os.path.join(manifest_dir, 'simple-service.yaml')
        )
        assert obj == simple_service

    def test_simple_service_wrong_type(self, manifest_dir):
        """Test loading the simple service to the wrong type."""
        with pytest.raises(ValueError):
            # The V1Container requires a name -- since the manifest has no name,
            # it will cause V1Container construction to fail with ValueError.
            manifest.load_type(
                client.V1Container,
                os.path.join(manifest_dir, 'simple-service.yaml')
            )

    def test_bad_path(self, manifest_dir):
        """Test specifying an invalid manifest path."""
        with pytest.raises(FileNotFoundError):
            manifest.load_type(
                client.V1Container,
                os.path.join(manifest_dir, 'foo', 'bar', 'baz.yaml')
            )

    def test_bad_yaml(self, manifest_dir):
        """Test specifying a file that is not valid YAML."""
        with pytest.raises(yaml.YAMLError):
            manifest.load_type(
                client.V1Container,
                os.path.join(manifest_dir, 'invalid.yaml')
            )