"use client"

import { useEffect, useState } from "react"
import { useReducedMotion } from "@/lib/use-reduced-motion"
import { cn, roleStyle, ROLE_SIGIL } from "@/lib/utils"
import type { AgentRole } from "@/types/api"

/* An authored, synthetic proceeding: the product doing its job in the first
   viewport. No real case, no real people. The newest line is struck forward
   with a solid ember edge; a custody line marks each claim cited / inferred /
   disputed; one citation is stitched to its source. */

type Prov = "cited" | "inferred" | "disputed"

interface Line {
  n: number
  role: string
  agentRole: AgentRole
  prov: Prov
  text: React.ReactNode
}

const SCRIPT: Line[] = [
  {
    n: 214,
    role: "Prosecution",
    agentRole: "prosecutor",
    prov: "cited",
    text: (
      <>
        The badge-reader log places the defendant on the ninth floor at{" "}
        <span className="tabular">23:41</span>, four minutes before the transfer
        cleared{" "}
        <span className="seam text-brass-text">access-log.csv, row 1180</span>.
      </>
    ),
  },
  {
    n: 215,
    role: "Defense",
    agentRole: "defense",
    prov: "disputed",
    text: (
      <>
        The same log shows the ninth-floor door held open for ninety seconds.
        Counsel has not established who walked through it.
      </>
    ),
  },
  {
    n: 216,
    role: "The Court",
    agentRole: "judge",
    prov: "inferred",
    text: (
      <>
        Noted. The inference of sole presence is not yet on the record. I want
        the corridor camera before we weigh it.
      </>
    ),
  },
  {
    n: 217,
    role: "Forensic Accountant",
    agentRole: "expert_witness",
    prov: "cited",
    text: (
      <>
        Spawned to trace the transfer. The funds split across three accounts
        within the hour, each under the reporting threshold{" "}
        <span className="seam text-brass-text">wire-ledger.pdf, p.12</span>.
      </>
    ),
  },
]

const PROV_TONE: Record<Prov, string> = {
  cited: "text-brass-text",
  inferred: "text-foreground/45",
  disputed: "text-oxblood-bright",
}

export function LiveRecord() {
  const reduce = useReducedMotion()
  const [shown, setShown] = useState(reduce ? SCRIPT.length : 1)

  useEffect(() => {
    if (reduce || shown >= SCRIPT.length) return
    const t = setTimeout(() => setShown((s) => s + 1), 1500)
    return () => clearTimeout(t)
  }, [shown, reduce])

  const streaming = !reduce && shown < SCRIPT.length

  return (
    <div className="relative w-full max-w-[540px]">
      <div className="overflow-hidden rounded-lg border border-border bg-ink-raised/85 shadow-chamber">
        <div className="flex items-center justify-between px-4 py-2.5 hairline-b">
          <span className="font-serif text-[0.8rem] text-foreground/60">
            Proceeding, courtroom mode
          </span>
          <span className="flex items-center gap-1.5 font-mono text-[0.66rem] uppercase tracking-wide text-ember-text">
            {streaming && <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-ember" />}
            on the record
          </span>
        </div>

        <div className="px-3 py-3 sm:px-4">
          {SCRIPT.slice(0, shown).map((line, i) => {
            const isNewest = i === shown - 1
            return (
              <div
                key={line.n}
                className={cn(
                  "record-line py-2.5",
                  i > 0 && "hairline-t",
                  isNewest ? "struck" : "afterglow",
                  isNewest && !reduce && "rec-enter",
                )}
                data-prov={line.prov}
              >
                <div className="lineno">{line.n}</div>
                <div className={cn("custody-line", isNewest && "arrive")} data-prov={line.prov}>
                  <div className="mb-1 flex items-center gap-2">
                    <span
                      className="grid h-[1.15rem] w-[1.15rem] place-items-center rounded-sm border font-mono text-[0.6rem] font-semibold"
                      style={roleStyle(line.agentRole)}
                    >
                      {ROLE_SIGIL[line.agentRole]}
                    </span>
                    <span className="font-serif text-[0.9rem] font-medium text-foreground">
                      {line.role}
                    </span>
                    <span className={cn("ml-auto font-mono text-[0.58rem] uppercase tracking-wide", PROV_TONE[line.prov])}>
                      {line.prov}
                    </span>
                  </div>
                  <p
                    className={cn(
                      "rec-body text-[0.86rem] leading-relaxed text-foreground/85",
                      isNewest && streaming && "streaming-cursor"
                    )}
                  >
                    {line.text}
                  </p>
                </div>
              </div>
            )
          })}
        </div>

        <div className="px-4 py-2 hairline-t">
          <span className="font-mono text-[0.62rem] text-foreground/45">
            Illustrative record. Synthetic case, no real parties.
          </span>
        </div>
      </div>
    </div>
  )
}
