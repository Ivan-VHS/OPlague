# USB tree dump

`tools/usb_tree_dump.py` creates a tree from a JSON export of USB Plug and Play
records. It is an offline formatter: it does not query or alter devices and it
does not install, load or modify drivers.

## Input and run

The input may be a JSON array or an object containing a `devices` array. Each
record needs an `instance_id` (or `InstanceId`) and may include
`parent_instance_id`, `name`, `status` and `service`.

```sh
python tools/usb_tree_dump.py devices.json
python tools/usb_tree_dump.py devices.json --show-instance-ids
```

Raw PnP Instance IDs are omitted by default because the final component can
contain a device serial number. The opt-in flag exposes those identifiers in
the output. Duplicate IDs, parent cycles, malformed bus prefixes and trees
deeper than the configured safety limit are rejected.
