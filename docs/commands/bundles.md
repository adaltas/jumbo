# Bundle commands

## Add bundle

**Command: `addbundle <name>`**

Add a bundle of services to the current cluster.

**Options**

- `--position POSITION` or `-p POISTION` - Specify the position of the bundle in the list of active bundles. Each bundle will be called one after another (consecutive calls of `deploy.yml`).
- `--cluster` or `-c` - The cluster to add the bundle to.

---

## Delete bundle

**Command: `rmbundle <name>`**

Delete a bundle of services from the current cluster.

**Options**

- `--cluster` or `-c` - The cluster to remove the bundle from.