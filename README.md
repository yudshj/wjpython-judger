# Usage

`./gen_tar.sh hw1 hw2 <code_dir_names> ...`

## Get Hash

```bash
#!/bin/bash

echo $(cat "$1" | tr -d '[:space:]' | sha512sum | cut -c-128) $1
```
