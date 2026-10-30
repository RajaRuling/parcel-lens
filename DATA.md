# Data provenance, acquisition and licence

Checked 2026-10-29. **No real parcel photographs were acquired or evaluated. Real-image performance and the synthetic-to-real gap are untested.** This is a negative acquisition outcome, not a claim that no suitable dataset exists.

## Search and acquisition log

Public search covered Hugging Face, a university/research archive, Zenodo, Figshare, Roboflow Universe and Wikimedia Commons. No account, credentials or private data were used. Initial network calls in the restricted shell failed DNS; retried public metadata with network access. No source-control service was accessed.

| Source and URL | Licence checked | Actual outcome and decision |
| --- | --- | --- |
| Damage Parcel, CSC649 — https://universe.roboflow.com/csc649-w35fl/damage-parcel | CC BY 4.0 on public search record | Retried the source, HTTP 403. No credential-free export obtained. Earlier attempt also failed. |
| BoxCondition, Ttttt — https://universe.roboflow.com/ttttt-xe3am/boxcondition-sfato | CC BY 4.0 on public search record; 3,972 advertised images | New classification candidate; direct HTTP 403. No image-plus-label export obtained. |
| HassanBinAli / Damaged_Parcel_boxes — https://huggingface.co/datasets/HassanBinAli/Damaged_Parcel_boxes | MIT metadata | Public dataset API and tree returned HTTP 200; train parquet only 17,258 bytes, test 5,036 bytes. Search viewer exposes local filesystem path strings, not embedded images. No images copied. API search for parcel and damaged also found a second text-only mirror; not an independent image source. |
| Parcel3D, Alexander Naumann, Felix Hertlein, Laura Dörr and Kai Furmans — https://zenodo.org/records/8032204 | Record explicitly restricts rendered images to academic research; textureless objects separately CC BY 4.0 | Zenodo API HTTP 200; 13,000+ synthetic images, not real photos. Rejected rendered imagery because the licence does not permit this general-use demo. |
| Container damage dataset, 张本硕 — https://doi.org/10.6084/m9.figshare.29539082.v1 | CC BY 4.0 verified in Figshare API | Figshare API HTTP 200, downloadable 60,556,372-byte archive, 640 annotated container images advertised. Metal freight-container damage is not cardboard parcel damage; not relabelled as a parcel benchmark. Archive not downloaded. |
| Wikimedia Commons — https://commons.wikimedia.org/wiki/Category:Damaged_cardboard_boxes and https://commons.wikimedia.org/wiki/Category:Deformed_cardboard_boxes | Individual file licences must be checked; category-page licence is not an image licence | Damaged category contains one snail-eaten cardboard image. Deformed category API HTTP 200: three views of one custom television shipping box, not three independent damaged parcels. These cannot form a balanced 100-image benchmark or reliable independent test. No files downloaded; no redistribution licence asserted for these files. |
| PackDet, industoai — https://huggingface.co/datasets/industoai/PackDet | CC BY-NC 4.0 on dataset card | Packaging segmentation, not damage labels; noncommercial limitation. Rejected. |
| Cardboard anomaly detection, Gabriel8 — https://huggingface.co/datasets/Gabriel8/cardboard-box-anomaly-detection | CC BY-NC-SA 4.0 in public dataset API | Newly found in cardboard search; noncommercial limitation unsuitable for a generally reusable demo. Not downloaded. |
| PackageDamage model card, Evan Ancheta — https://huggingface.co/cvtechniques/PackageDamage | MIT model card | A model, not a credential-free independently licensed image dataset. Card reports third-party training data; its model metrics are not reproduced and are not presented as this project's results. |

Public API discovery also searched `parcel`, `damaged`, `package-damage`, `boxcondition` and `cardboard` on Hugging Face. Unrelated robotics, land-parcel, vehicle and media-damage records were excluded. An AI-generated ecommerce collection surfaced in search; generated photos would not establish real-image performance and were not used. Licence pages: https://creativecommons.org/licenses/by/4.0/ , https://creativecommons.org/licenses/by-nc/4.0/ . No external image attributions are required in the gallery because every displayed image is original procedural data.

## Version 2 data actually used

Name: Parcel Lens procedural scenes v2. Created locally 2026-10-29; no download date or external image URL applies. Images and annotations: CC0 1.0, https://creativecommons.org/publicdomain/zero/1.0/ ; see data/LICENSE.txt. No outside textures, logos, stock images or model-generated images.

4,800 PNG scenes, 224 × 168. Splits are assigned before rendering and persisted to data/v2/split-plan.json: 2,400 training (seeds 120000–122399), 600 validation (220000–220599), 900 standard test (320000–320899), 900 shift test (420000–420899). Each unique source scene has exactly one image; no crops or augmented siblings cross splits. SHA-256 of every image is in the manifest. All splits contain 50% clean scenes and 10% of each of five damage types. This engineered prevalence is not a field estimate.

Types: dent/crush, tear/puncture, water stain, open flap and crushed corner. Damage severity is an input rendering strength, not a human injury or loss grade. Lighting is dim, neutral or bright. Randomized nuisance factors include cardboard colour, fibrous marks, side/top-face depth, rotated viewpoint, background palette and gradient, tape placement, printed label/barcodes, harmless scuffs, partial tape occlusion, brightness gradient, blur and sensor noise. Shift scenes hold out cooler colour cast, larger rotation, darker mixed backgrounds, clutter and stronger noise together; this bundles multiple shifts and cannot isolate their individual causal effects. These are simplified 2D drawings, not physically based renders.

Annotations: generated algorithmically from intended class and a raster damage mask; no human annotations or independent human quality review. Boxes are exclusive-right/bottom xyxy mask bounds after rotation; water-stain blur may expand bounds. Tape can hide damage while the intent remains labelled positive, creating an inherently ambiguous observable task. Binary image classification is the measured learned task. Neither learned localization, real damage severity estimation nor damage-type classification is established.

## Legacy material

The original 40 synthetic illustrations and their old detector results remain in data/ for regression tests. They are excluded from every version 2 train/validation/test total. Version 1 docs and example assets are replaced by version 2; no old accuracy number is used as new evidence.

## Optional local vision experiment

Inspected Tools/private_vision.py: it stages image attachments for the application's private chat and declares vision capability; it is not a standalone credential-handling inference client. The existing project adapter needs explicit endpoint/model configuration. No safe, configured, same-machine inference route was verified without reading restricted credential configuration or using another machine. No inference request, model swap or GPU job was made. Vision-model agreement remains untested; agreement would not substitute for independent truth.
