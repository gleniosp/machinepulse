# ADR-0003 — Device and asset identifiers

- **Status:** Accepted
- **Date:** 2026-10-13
- **Decision owners:** Project maintainer
- **Related requirements:** FR-001, FR-002, FR-007, FR-012, FR-024, NFR-002, NFR-011
- **Related specifications:** [Telemetry contract](../specs/telemetry-contract.md#device-and-asset-id-profile), [Simulator behavior](../specs/simulator.md#run-configuration)
- **Related product document:** [Domain model — Entity identity lifecycle](../product/domain-model.md#entity-identity-lifecycle)
- **Related experiments:** None; format and interoperability review, not a performance benchmark
- **Supersedes:** None; complements [ADR-0001](0001-telemetry-event-identifiers.md)
- **Superseded by:** None

## Context

Before this review, the simulator and `telemetry.v1` validator required
non-empty device and asset IDs but did not define a format. Examples such as
`device-0001` and `asset-0001` are convenient locally but can collide when
independently configured producers or datasets meet. These IDs will become
durable joins between telemetry, operational records, and maintenance history.

An event identifies one window; a device identifies a producer; an asset
identifies a maintainable object. Device and asset IDs are allocated far less
often than event IDs. They need stable identity and independent allocation,
but their creation order does not determine telemetry order. The maintainer
prefers ULID's shorter text representation. The platform may eventually span
millions of devices, customers, locations, and assets, so hierarchy, ownership,
and authorization must remain separate from the ID.

## Selection criteria

Evaluate each entity independently of the event-ID format:

| Need                     | Device ID                                                    | Asset ID                                                           |
| ------------------------ | ------------------------------------------------------------ | ------------------------------------------------------------------ |
| Stable identity          | Survives producer restart, update, and reassignment          | Survives rename, repair, and relocation                            |
| Independent allocation   | Provisioning and simulator configuration can work offline    | Separate installations can create records without a shared counter |
| Immutable input          | Must not depend on address, credentials, or software version | Must not depend on name, location, or current device               |
| Practical representation | Bounded, safe to copy into config, compact in telemetry      | Bounded, suitable for durable references and joins                 |
| Creation ordering        | Not used for event ordering                                  | Not used for asset chronology                                      |
| Human-facing labels      | Device label remains separate metadata                       | Customer number, name, and physical tag remain separate metadata   |

Both have occasional allocation followed by many references. A high telemetry
rate does not mean a high entity-ID allocation rate. There is no measured
entity-table insert bottleneck or required chronological ID scan. Compact text
is a stated preference; it does not by itself require ordered IDs.

## Decision

Use ULID for both `device_id` and `asset_id` as opaque MachinePulse entity
keys. Use a canonical 26-character uppercase Crockford Base32 form, without
type prefixes. It is ten characters shorter than canonical UUID text and can
be allocated independently without a shared counter. The timestamp component
makes allocation time approximate and visible; this decision accepts that
trade-off for the shorter representation. The timestamp is not a commissioning
date, event time, or ordering authority.

### Validation profile

Apply the same profile to simulator configuration and telemetry payloads:

- Require exactly 26 uppercase characters from the Crockford Base32 alphabet
  `0123456789ABCDEFGHJKMNPQRSTVWXYZ`.
- Require the first character to be `0` through `7`, which rejects values above
  the 128-bit ULID maximum `7ZZZZZZZZZZZZZZZZZZZZZZZZZ`.
- Reject lowercase, whitespace, prefixes, normalization, invalid characters,
  and non-string inputs.
- Validate syntax at the producer boundary. Parsing cannot establish entity
  existence, tenant ownership, enrollment, or an authorized device-to-asset
  association; those require retained operational state.

The exact wire-field requirements are owned by the
[telemetry contract](../specs/telemetry-contract.md#device-and-asset-id-profile).
The simulator configuration and telemetry validator implement this profile.

Allocate each ID once when creating or provisioning an entity, persist it,
and supply it to producers through configuration. Use a conforming generator
with uniform random suffixes from a cryptographically secure random source.
Creation tooling may run offline, but must not substitute a weak PRNG if
secure randomness is unavailable. Physical devices can receive an ID during
provisioning, so embedded firmware need not generate one. A simulator receives
fixed IDs from its configuration; it must not generate new entity IDs on every
run. Version 0.1 needs no provisioning service.

### Scale, uniqueness, and storage

ULID has 128 bits: a 48-bit Unix-millisecond timestamp and an 80-bit random
suffix. For one million independently generated IDs in the same millisecond,
the birthday-bound collision estimate is about 4.1 × 10⁻¹³. This estimate
assumes independent, uniformly random suffixes; it is not a guarantee and does
not cover cloned or faulty generators. Fleet size alone is not the risk
measure: IDs are allocated once, while collision probability depends on how
many are generated in the same millisecond. Persistent storage must still
enforce uniqueness and report conflicts. Never silently merge records or
change an already published ID after a conflict.

ULID and UUID both have 16-byte binary representations. The text form is
shorter, but does not reduce binary key size. PostgreSQL has a native `uuid`
type, not a native ULID type; do not label ULID bytes as UUIDs. The storage
schema should choose either validated canonical text or an explicit 16-byte
representation and account for primary-key, foreign-key, and index costs.
Benchmark that representation with actual access patterns when the schema is
designed; this decision makes no database performance claim.

### Entity relationships and customer boundaries

Do not encode customer, site, location, entity type, or asset hierarchy in an
ID. Model ownership and relationships as data with explicit constraints. If
multi-tenancy is introduced, every lookup and write must enforce tenant scope;
knowing or guessing an ID does not grant access. Locations and customer asset
numbers can change without changing the asset's canonical identity.

Distinct installations can allocate different keys for the same physical
motor; format-level uniqueness does not solve reconciliation. Preserve trusted
external asset identities and map them to MachinePulse records according to
the domain identity lifecycle. A physical tag can carry an internal ID or a
URL to the record; replacing a tag does not create a new asset.

## Alternatives considered

| Format                           | Allocation and text                                                     | Fit for MachinePulse                                                                                               |
| -------------------------------- | ----------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------ |
| ULID                             | Millisecond time plus 80 random bits; 26-character Base32 text          | Selected: compact standard representation; accepts approximate allocation-time disclosure and non-global ordering  |
| UUIDv4                           | Clock-independent random generation; 36-character text; 122 random bits | Strong opaque alternative with native PostgreSQL support and no timestamp disclosure                               |
| UUIDv7                           | Millisecond time plus up to 74 random bits; 36-character text           | Strong option for sustained ordered inserts; no entity-table bottleneck is established here                        |
| Nano ID (default secure profile) | Clock-independent random generation; 21-character text; 126 random bits | Shorter opaque alternative; requires a project-defined alphabet and profile across producers and consumers         |
| UUIDv5 from a name               | Repeatable generation from a namespace and name                         | Useful for events with a fixed input tuple; risky as an entity key when names or external tags change              |
| Counter or human-readable tag    | Compact; needs an allocation scope                                      | Useful as display or external metadata; insufficient as an independently allocated canonical identity              |
| Manufacturer/global asset URI    | Existing issuer-scoped identity                                         | Preserve for reconciliation and interoperability; cannot be assumed present for every simulated or physical entity |

ULID's timestamp comes from the allocator's clock. Clock skew can make
different producers' IDs appear out of order, and independent random
generators do not establish a global sequence. A monotonic generator orders
same-millisecond values only within its own state. Consumers must use explicit
timestamps and the device-local `sequence` for event chronology. The 48-bit
timestamp range is not a practical fleet-size limit.

The ULID specification accepts lowercase text, but this decision selects
uppercase as MachinePulse's one canonical wire representation. Reject wrong
lengths, characters outside the Crockford alphabet, lowercase, whitespace,
prefixes, and values above `7ZZZZZZZZZZZZZZZZZZZZZZZZZ`; do not silently
normalize. The identifier field and application type establish whether a
value is a device or asset ID; the ULID itself does not encode entity type.

### Compact opaque random strings

[Nano ID](https://github.com/ai/nanoid) demonstrates that clock-independent
random allocation can be shorter still: its default secure profile uses 21
URL-safe characters and 126 random bits. It avoids timestamp disclosure but
requires MachinePulse to define one alphabet, length, comparison, generation,
and storage profile across producers and consumers. ULID is selected for its
fixed standardized representation and broad independent implementation
profile, while accepting its timestamp trade-off. Do not invent a custom
random-ID generator.

### Natural identifiers and industrial asset references

Do not derive a new internal entity identity from display names, asset
locations, MAC addresses, or serial numbers. These belong in separate metadata
and can change, be duplicated, or come from different vendor scopes. Keep
human-friendly labels, customer numbering, and integration identifiers
separate from canonical IDs. UUIDv5 remains appropriate for the simulator's
event tuple in ADR-0001.

An existing, trusted global asset identity deserves different treatment from
a mutable label. OPC UA Asset Management Basics requires `ProductInstanceUri`
for global asset identification and permits a writable asset tag. The AAS
metamodel distinguishes `globalAssetId` from other scoped identifiers. These
support preserving external identities and their issuer/scheme; neither
specification selects ULID versus UUID for MachinePulse's internal references.
Version 0.1 also creates simulated assets and has no cross-company asset
interchange requirement. Use a separate internal key with preserved
external references; mapping APIs remain later capability work.

The reviewed Tractian glossary describes data standardization, asset numbers,
tags, registers, and hierarchies. It supports keeping a stable record identity
separate from customer-facing labels, physical tags, and site/location
relationships; it does not prescribe ULID, UUID, or a database key format.
[Data collection standardization](https://tractian.com/en/glossary/data-collection-standardization),
[asset tagging](https://tractian.com/en/glossary/asset-tagging),
[asset numbering](https://tractian.com/en/glossary/asset-numbering-system),
[asset register](https://tractian.com/en/glossary/asset-register), and
[asset hierarchy](https://tractian.com/en/glossary/asset-hierarchy).

## Consequences

### Positive

- Both entity types can be allocated independently without a shared counter.
- Canonical text is 26 characters, works in configuration and payload fields,
  and contains no customer, location, or mutable business attribute.
- Producers can retain their assigned identity while disconnected.
- Fixed configured IDs preserve simulator replay without an entity-ID service.
- Names, tags, and device-to-asset associations can change independently.

### Negative or accepted trade-offs

- The ID reveals approximate allocation time. Its ordering is not global or
  authoritative; clock skew and separate generators can reorder values.
- Each timestamp bucket has an 80-bit random suffix, compared with UUIDv4's
  122 random bits without time bucketing. Secure randomness and unique
  constraints remain required.
- PostgreSQL has no native ULID type. Storage must choose validated text or an
  explicit binary representation; text is shorter than UUID text but binary
  ULID and UUID keys are both 16 bytes.
- Opaque persistent IDs still allow correlation and are not secrets. An ID
  format does not ensure enrollment, tenant isolation, authorization, or a
  correct device-to-asset association.

### Follow-up work

This branch applies the selected ULID profile to simulator configuration,
telemetry validation, examples, and repeatability fixtures. Replacing
`device_id` changes the deterministic UUIDv5 event IDs derived from
`(device_id, run_id, sequence)`; migrated runs are not byte-identical replays
of outputs produced with the former IDs.

Before release, review compatibility for any consumer that uses the former
free-form values. If those values have crossed a released contract boundary,
use an explicit migration or versioning plan rather than silently narrowing
`telemetry.v1`. Ingestion/storage work still needs enrollment,
unique constraints, key representation and index strategy, tenant-scoped
authorization, association history, and authenticated producer-to-device
mapping. A syntactically valid ID alone must not register a new entity.

## Follow-up validation

Provisioning tooling must support secure ULID generation and strict
validation. Implementation evidence should reject invalid alphabet, case,
length, and overflow; retain configured IDs across restart and replay; and
distinguish renaming, reassignment, and replacement. Storage evidence should
cover uniqueness, reference integrity, key representation, and conflicts;
ingestion evidence should cover tenant-scoped authorization and unknown
producer references. If entity creation becomes frequent, benchmark actual
tables and access patterns before choosing text versus binary storage or
prioritizing ordered IDs. No runtime or database performance claims are
established by this documentation review.

## References

- [ULID canonical specification](https://github.com/ulid/spec): encoding, timestamp/random layout, monotonic generation, and overflow validation.
- [RFC 9562: UUIDv4](https://www.rfc-editor.org/rfc/rfc9562.html#section-5.4), [UUIDv7](https://www.rfc-editor.org/rfc/rfc9562.html#section-5.7), and best practices for generation, clocks, randomness, opacity, and database storage.
- [Nano ID](https://github.com/ai/nanoid): compact secure random allocation with a default URL-safe alphabet and configurable profiles.
- [OPC UA asset identification](https://reference.opcfoundation.org/specs/OPC-10000-110/7) and [AAS identifier guidance](https://industrialdigitaltwin.io/aas-specifications/IDTA-01001/v3.1.1/annex/general.html): global industrial identities and other scoped identifiers.
- [NIST AMS 300-12](https://nvlpubs.nist.gov/nistpubs/ams/NIST.AMS.300-12.pdf), abstract and section 4.5.1: persistent identifiers alongside human-readable designations in product lifecycle data; not a prescription for MachinePulse's identifier format.
- [AWS IoT device management](https://docs.aws.amazon.com/iot/latest/developerguide/iot-thing-management.html): registry identity with separate manufacturer/serial attributes; a lifecycle example, not a requirement to adopt AWS.
- Tractian glossary: [data collection standardization](https://tractian.com/en/glossary/data-collection-standardization), [asset tagging](https://tractian.com/en/glossary/asset-tagging), [asset numbering](https://tractian.com/en/glossary/asset-numbering-system), [asset register](https://tractian.com/en/glossary/asset-register), and [asset hierarchy](https://tractian.com/en/glossary/asset-hierarchy). These inform separation of entity records, labels, tags, and hierarchy, not the ID format.
- [PostgreSQL UUID type](https://www.postgresql.org/docs/17/datatype-uuid.html): native storage for UUIDs; PostgreSQL does not define a native ULID type.

Sources reviewed on 2026-10-13. The selected format and lifecycle policy are
MachinePulse design decisions based on these sources and repository needs.
