# Third-party software provenance

The network simulator modifications in this archive are based on SimBlock by the Distributed Systems Group, Tokyo Institute of Technology.

- Upstream: https://github.com/dsg-titech/simblock
- Base commit: `8a1285aa37b832385b0be2ae6f804885a4a7031f`
- Upstream license: Apache License 2.0

The included Java files retain their upstream copyright/license headers. `NetworkConfiguration.java` is included only as an unmodified reference for the network defaults used in the experiments.


## Polkadot SDK Solochain Template
The execution-testbed code is based on the Polkadot SDK Solochain Template at commit `2610f22b838f65bfeec9791ede17827b74e1ac50` (stable2503). The archive includes only the local patch, custom `pallet-pqc-bench`, harness/test vectors and exact experimental binaries. Consult the upstream repository and individual crate/source headers for the applicable third-party licenses before choosing a license for the Zenodo deposit.
