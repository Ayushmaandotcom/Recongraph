# ReconGraph — Project Definition

## 1. Project Overview

ReconGraph is an explainable financial reconciliation and exception-investigation engine.

The system identifies records across different financial evidence sources that may represent the same underlying financial event, detects inconsistencies between those records, and investigates probable causes of reconciliation failures.

ReconGraph is based on a simple idea:

> Financial documents and system records are not the financial event itself. They are evidence describing an underlying financial event.

For example, a single business purchase may produce:

* a vendor invoice;
* a purchase-register entry;
* a GST record; and
* a bank transaction.

These records may use different vendor names, invoice-number formats, dates, and references even when they describe related financial activity.

ReconGraph attempts to connect this evidence and explain where it disagrees.

---

## 2. Core Product Question

> Why does the money not match?

ReconGraph attempts to answer four questions:

1. Which financial records appear to describe the same underlying financial event?
2. Where do related financial records disagree?
3. What is the probable cause of the disagreement?
4. Can multiple reconciliation exceptions be explained by the same systemic pattern?

---

## 3. Initial Problem Scope

The initial prototype focuses on purchase-side financial reconciliation.

The first supported financial evidence types are:

* invoice records;
* purchase-register entries;
* GST records; and
* bank transactions.

The initial matching engine will focus on one-to-one financial-record relationships.

Many-to-one and one-to-many financial relationships will be explored in later milestones.

---

## 4. Core Concepts

### Financial Event

A real-world economic activity that may produce multiple financial records.

Example:

A company purchases goods from a vendor and subsequently pays the vendor.

### Financial Evidence Record

A structured or unstructured record that provides evidence about a financial event.

Examples include:

* an invoice;
* a purchase-register entry;
* a GST record; or
* a bank transaction.

### Candidate Relationship

A possible relationship between two financial evidence records.

A candidate relationship does not imply that the records have been confirmed to represent the same financial event.

### Financial Relationship Score

An explainable score representing the strength of available evidence that two financial records are related.

The initial Financial Relationship Score may consider:

* amount compatibility;
* entity compatibility;
* reference compatibility;
* temporal compatibility; and
* tax-identity compatibility.

### Reconciliation Exception

A disagreement, missing relationship, or unexplained financial record discovered during reconciliation.

### Exception Investigation

The process of analyzing available evidence to identify a probable cause for a reconciliation exception.

### Resolution Proposal

A suggested explanation or corrective action for an exception.

A resolution proposal is not automatically applied to an accounting or financial system.

---

## 5. Initial Hypothesis

Financial records representing the same underlying financial event can be identified using a combination of:

* deterministic normalization;
* fuzzy entity matching;
* reference matching;
* temporal constraints;
* tax identity; and
* relationship-specific scoring.

An evidence graph can subsequently represent discovered financial relationships and support the investigation of more complex reconciliation failures.

---

## 6. System Principles

### Explainability Before Automation

Important matching decisions must expose their contributing signals.

ReconGraph should not only state that two records are probably related. It should explain why.

### Missing Data Is Not Contradictory Data

An unavailable value must be represented separately from a conflicting value.

For example, a missing GSTIN is not equivalent to two different GSTIN values.

### Relationship Context Matters

The expected relationship between an invoice and a GST record differs from the expected relationship between an invoice and a bank transaction.

Matching logic should account for the relationship type being evaluated.

### Deterministic Baseline First

The initial matching engine will be deterministic and measurable before language models are introduced.

### AI Is an Investigation Component

Language models may later assist with:

* document extraction;
* exception explanation;
* root-cause summarization; and
* investigation workflows.

Language models will not be treated as the source of financial truth.

### Source Records Remain Immutable

ReconGraph should preserve original financial evidence records.

Normalization, discovered relationships, analytical results, and proposed resolutions should exist as derived data.

---

## 7. MVP Non-Goals

The initial prototype will not:

* replace accounting software;
* file GST returns;
* directly modify Tally or ERP records;
* automatically move money;
* determine legal or tax compliance;
* train a proprietary foundation model;
* support every financial workflow;
* perform real-time bank integration; or
* automatically apply reconciliation corrections.

---

## 8. Initial Technical Success Criteria

The first prototype should:

1. load structured purchase-register and GST records;
2. normalize financial identifiers and vendor names;
3. generate plausible candidate record pairs;
4. calculate individual matching signals;
5. dynamically normalize signal weights when data is unavailable;
6. produce an explainable Financial Relationship Score;
7. rank probable financial relationships;
8. distinguish high-confidence matches from ambiguous candidates; and
9. evaluate predicted relationships against known ground truth.

---

## 9. Long-Term Technical Direction

ReconGraph may evolve into a financial evidence graph capable of:

* multi-source financial reconciliation;
* many-to-one settlement matching;
* one-to-many financial relationships;
* exception classification;
* systemic root-cause clustering;
* reconciliation replay;
* financial evidence visualization; and
* AI-assisted exception investigation.

---

## 10. Project Identity

ReconGraph is not an accounting chatbot.

ReconGraph is not a GST filing application.

ReconGraph is not a generic document question-answering system.

ReconGraph is an explainable financial evidence and exception-investigation engine focused on understanding why financial records fail to reconcile.
