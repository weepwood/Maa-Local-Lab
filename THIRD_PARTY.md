# MXU / MaaFramework third-party notices

Maa Local Lab uses the **original MXU frontend binary** unchanged as its GUI. We do not claim ownership of upstream MXU.

| Component | Version | License | Corresponding source |
| --- | --- | --- | --- |
| MXU (MistEO) | v2.7.1, `9fa8cc51e8ff8cd89d99f3ea55fe3a7a82e6ede3` | GNU AGPL-3.0 | https://github.com/MistEO/MXU/tree/v2.7.1 |
| MaaFramework (MaaXYZ) | v5.14.3, `8963191215ca49d6b037802acd07d20a4213160a` | GNU LGPL-3.0 | https://github.com/MaaXYZ/MaaFramework/tree/v5.14.3 |

This project distributes the unmodified upstream MXU executable along with an independent automation project (PI V2 `interface.json`, pipeline, and test-target executable). The upstream GUI is AGPL-3.0, while MaaFramework is LGPL-3.0. The Windows package includes copies of their licenses in `licenses/`. The upstream sources (including build instructions and the exact release source revision) are linked above.

Third-party components contained in upstream archives may have additional notices. Refer to the upstream source repositories.

If you distribute a modified version of MXU in the future, satisfy AGPL-3.0 corresponding-source obligations for the modified version as well. Upstream MXU automatically requests elevation on Windows release launches; evaluate this for the intended use.
