# WP18BR3 Five-Year Review

Date: 2026-08-03

## Purpose

Expand the BR2 regret review and answer four questions:

1. What becomes technical debt?
2. What becomes organizational debt?
3. What becomes operational debt?
4. What becomes AI debt?

## What becomes technical debt if left alone

1. **Enterprise hierarchy trapped inside governance but not propagated into readers.**  
   Governance already models enterprise scope, while ODS/KPI/AI readers still default to MASCI-only assumptions. That gap will harden into exception-driven architecture.  
   Evidence: `backend/services/enterprise_governance.py:202-233,858-905,1536-1551`; `backend/routes/ods_intelligence.py:29,75-83`; `backend/routes/operational_kpis.py:173-187`; `backend/routes/ai_admin_config.py:47-52`

2. **Executive reporting overlap becoming the platform’s semantic tax.**  
   ODS, Project Health, KPI rollups, executive overview, and legacy operational intelligence all carry real value, but too many adjacent read models will eventually slow decision-making.

3. **Treating P&L snapshot and PO amounts as if they were a finance operating system.**  
   That would create an expensive second truth later when controller-grade budget and actual-cost governance arrive.

## What becomes organizational debt if left alone

1. Executives learning multiple dashboard dialects for similar questions.
2. Operations leaders carrying informal knowledge about where “the real answer” lives.
3. HR, PM, dispatch, and shop leaders translating resource truth manually across systems.
4. Accounting/finance relying on operational proxies instead of a coherent financial model.

## What becomes operational debt if left alone

1. Constraint exceptions being explained in meetings instead of resolved in one explicit operational contract.
2. Resource loading staying understandable only to insiders who already know the unofficial federation between planning, roster, and dispatch.
3. Equipment lifecycle context remaining slightly fragmented at the registry/provider edge.
4. Executive rollups growing slower and less trusted as portfolio scale increases.

## What becomes AI debt if left alone

1. AI consuming ambiguous upstream truths and scaling the ambiguity faster.
2. Pressure to let AI explain or summarize finance domains that still have no canonical owner.
3. Expansion of briefing/intelligence surfaces before the reporting hierarchy is simplified.

## Things we will regret leaving alone

1. Executive reporting overlap
2. Enterprise hierarchy propagation gaps
3. Absence of Budget Hierarchy
4. Absence of Earned Value

## Things we will regret rebuilding

1. project identity / `jobs_master`
2. cost-code registry
3. project cost-code planning and schedule foundation
4. daily-report field capture
5. team roster authority
6. Asset Spine registry core
7. governance/audit backbone

## Things we will regret making too complex

1. creating a second or third executive reporting stack
2. inventing a separate planning database when `jobs_master.assigned_cost_codes` already exists
3. overfitting multi-company abstractions before current governance propagation is fully leveraged

## Things we will regret making too simple

1. pretending a labor-rate input and approved PO amounts equal enterprise finance authority
2. flattening production into one number without fact-family boundaries
3. treating enterprise scope as “just a tenant field” when governance already models richer hierarchy

## Things competitors will eventually do better if unchanged

1. unified executive reporting with one portfolio truth hierarchy
2. controller-grade budget / actual-cost / EV integration
3. enterprise-wide cross-company resource and equipment planning

## Things AI will replace

1. repetitive summarization and translation
2. parts of executive briefing and queue prioritization
3. low-value reconciliation explanation work once canonical truths are locked

## Things humans should always own

1. budget authority and approval accountability
2. enterprise hierarchy and organizational responsibility
3. operational override decisions
4. safety-critical and high-liability control decisions
5. final executive interpretation of financial and project-control exceptions

## BR3 five-year conclusion

The greatest five-year mistake would not be failing to invent more architecture.  
It would be **failing to preserve the right architecture while tightening the few domains that are still constitutionally weak**.