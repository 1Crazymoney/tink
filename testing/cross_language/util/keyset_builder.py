# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Python implementation of a KeysetBuilder."""

# Placeholder for import for type annotations

import io
import random
import tink
from tink import cleartext_keyset_handle
from tink.proto import tink_pb2

_MAX_INT32 = 4294967295  # 2^32-1


def _new_key_data(key_template: tink_pb2.KeyTemplate) -> tink_pb2.KeyData:
  return tink.core.Registry.new_key_data(key_template)


def _generate_unused_key_id(keyset: tink_pb2.Keyset) -> int:
  while True:
    key_id = random.randint(1, _MAX_INT32)
    if key_id not in {key.key_id for key in keyset.key}:
      return key_id


# TODO(juerg) Remove this, and use the version in tink/python/tink/testing.


class KeysetBuilder(object):
  """A KeysetBuilder provides convenience methods for managing Keysets.

  It provides methods for adding, disabling, enabling, or deleting keys.
  The validity of the keyset is checked when creating a keyset_handle.
  """

  def __init__(self, keyset_proto: tink_pb2.Keyset):
    self._keyset = keyset_proto

  def keyset_handle(self) -> tink.KeysetHandle:
    keyset_copy = tink_pb2.Keyset()
    keyset_copy.CopyFrom(self._keyset)
    return cleartext_keyset_handle.from_keyset(keyset_copy)

  def keyset(self) -> bytes:
    return self._keyset.SerializeToString()

  def add_new_key(self, key_template: tink_pb2.KeyTemplate) -> int:
    """Generates a new key, adds it to the keyset, and returns its ID."""
    new_key = self._keyset.key.add()
    new_key.key_data.CopyFrom(_new_key_data(key_template))
    new_key.status = tink_pb2.ENABLED
    new_key_id = _generate_unused_key_id(self._keyset)
    new_key.key_id = new_key_id
    new_key.output_prefix_type = key_template.output_prefix_type
    return new_key_id

  def set_primary_key(self, key_id: int) -> None:
    """Sets a key as primary."""
    for key in self._keyset.key:
      if key.key_id == key_id:
        self._keyset.primary_key_id = key_id
        return
    raise tink.TinkError('key not found: %d' % key_id)

  def enable_key(self, key_id: int) -> None:
    """Enables a key."""
    for key in self._keyset.key:
      if key.key_id == key_id:
        key.status = tink_pb2.ENABLED
        return
    raise tink.TinkError('key not found: %d' % key_id)

  def disable_key(self, key_id: int) -> None:
    """Disables a key."""
    for key in self._keyset.key:
      if key.key_id == key_id:
        key.status = tink_pb2.DISABLED
        return
    raise tink.TinkError('key not found: %d' % key_id)

  def delete_key(self, key_id: int) -> None:
    """Deletes a key."""
    for key in self._keyset.key:
      if key.key_id == key_id:
        self._keyset.key.remove(key)
        return
    raise tink.TinkError('key not found: %d' % key_id)


def from_keyset(keyset: bytes) -> KeysetBuilder:
  """Return a KeysetBuilder for a Keyset copied from a KeysetHandle."""
  keyset_proto = tink_pb2.Keyset()
  keyset_proto.ParseFromString(keyset)
  return KeysetBuilder(keyset_proto)


def from_keyset_handle(keyset_handle: tink.KeysetHandle) -> KeysetBuilder:
  """Return a KeysetBuilder for a Keyset copied from a KeysetHandle."""
  keyset_buffer = io.BytesIO()
  cleartext_keyset_handle.write(
      tink.BinaryKeysetWriter(keyset_buffer), keyset_handle)
  return from_keyset(keyset_buffer.getvalue())


def new_keyset_builder() -> KeysetBuilder:
  return KeysetBuilder(tink_pb2.Keyset())
