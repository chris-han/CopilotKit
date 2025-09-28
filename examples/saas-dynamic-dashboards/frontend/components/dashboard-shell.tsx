"use client"

import type { ReactNode } from "react"

import { usePathname } from "next/navigation"
import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
} from "@/components/ui/sidebar"
import { ModeToggle } from "@/components/mode-toggle"
import { Code2, FlaskConical, LayoutDashboard, LogOut, Settings, TestTube2, TrendingUp } from "lucide-react"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import Link from "next/link"
import { useCopilotChat, useCopilotReadable } from "@copilotkit/react-core"
import { devSuggestions, generalSuggestions, testerPersonaSuggestions } from "@/lib/prompts"
import { useSharedContext } from "@/lib/shared-context"
import { useCopilotChatSuggestions } from "@copilotkit/react-ui"
import { useSharedTestsContext } from "@/lib/shared-tests-context"
import { useEffect, useMemo, useRef, useState } from "react"

type UserRole = "developer" | "tester" | "lab-admin" | "executive" | "general"

const ROLE_LABELS: Record<UserRole, string> = {
  developer: "Developer",
  tester: "Tester",
  "lab-admin": "Lab Admin",
  executive: "Executive",
  general: "General",
}

const deriveRoleFromTitle = (title: string): UserRole | null => {
  const normalized = title.toLowerCase()

  if (normalized.includes("tester")) return "tester"
  if (normalized.includes("developer")) return "developer"
  if (normalized.includes("lab admin") || normalized.includes("lab-admin")) return "lab-admin"
  if (normalized.includes("executive")) return "executive"

  return null
}

export function DashboardShell({ children }: { children: ReactNode }) {
  const { prData } = useSharedContext()
  const { testsData } = useSharedTestsContext()
  const pathname = usePathname()
  const [userRole, setUserRole] = useState<UserRole>(() => {
    if (typeof document !== "undefined") {
      return deriveRoleFromTitle(document.title) ?? "general"
    }
    return "general"
  })
  const { reset } = useCopilotChat()
  const lastRoleRef = useRef<UserRole>(userRole)
  const lastInstructionsRef = useRef<string | null>(null)
  const lastDataSignatureRef = useRef<{ pr: string; tests: string }>({ pr: "", tests: "" })

  useEffect(() => {
    if (typeof document === "undefined") return

    const updateRoleFromTitle = () => {
      const nextRole = deriveRoleFromTitle(document.title) ?? "general"
      setUserRole((current) => (current === nextRole ? current : nextRole))
    }

    updateRoleFromTitle()

    const titleElement = document.head?.querySelector("title")
    if (!titleElement) {
      return
    }

    const observer = new MutationObserver(updateRoleFromTitle)
    observer.observe(titleElement, { subtree: true, characterData: true, childList: true })

    return () => {
      observer.disconnect()
    }
  }, [])

  const prDataSignature = useMemo(() => JSON.stringify(prData ?? []), [prData])
  const testsDataSignature = useMemo(() => JSON.stringify(testsData ?? []), [testsData])

  useCopilotReadable(
    {
      description: "PR_DATASET",
      value: prData,
    },
    [prData]
  )

  useCopilotReadable(
    {
      description: "TEST_SUITE_DATASET",
      value: testsData,
    },
    [testsData]
  )

  useCopilotReadable(
    {
      description: "CURRENT_USER_ROLE",
      value: userRole,
    },
    [userRole]
  )

  const prCount = prData?.length ?? 0
  const testsCount = testsData?.length ?? 0
  const displayedRole = ROLE_LABELS[userRole]

  const suggestionInstructions = useMemo(() => {
    const baseInstructions =
      userRole === "tester"
        ? testerPersonaSuggestions
        : userRole === "developer"
          ? devSuggestions
          : generalSuggestions

    const dataHint =
      userRole === "tester"
        ? "Use the Copilot readable named \"TEST_SUITE_DATASET\" for the latest generated or selected QA test suites."
        : "Use the Copilot readable named \"PR_DATASET\" for the current pull request portfolio."

    const datasetSummary =
      userRole === "tester"
        ? `There are ${testsCount} QA test suites currently in context.`
        : `There are ${prCount} pull request records currently in context.`
    return `${baseInstructions}\n\nCURRENT_USER_ROLE: ${userRole}\n${dataHint}\n${datasetSummary}`
  }, [userRole, prCount, testsCount])

  useEffect(() => {
    const instructionsChanged = lastInstructionsRef.current !== suggestionInstructions
    const roleChanged = lastRoleRef.current !== userRole
    const prChanged = lastDataSignatureRef.current.pr !== prDataSignature
    const testsChanged = lastDataSignatureRef.current.tests !== testsDataSignature
    const dataChanged = prChanged || testsChanged

    if (roleChanged) {
      reset()
    }
    if (roleChanged || instructionsChanged || dataChanged) {
      if (roleChanged) {
        lastRoleRef.current = userRole
      }
      if (instructionsChanged) {
        lastInstructionsRef.current = suggestionInstructions
      }
      if (prChanged) {
        lastDataSignatureRef.current.pr = prDataSignature
      }
      if (testsChanged) {
        lastDataSignatureRef.current.tests = testsDataSignature
      }
    }
  }, [userRole, suggestionInstructions, prDataSignature, testsDataSignature, reset])
  const routes = [
    {
      title: "Developer",
      href: "/developer",
      icon: Code2,
      isActive: pathname === "/developer" || pathname === "/",
    },
    {
      title: "Tester",
      href: "/tester",
      icon: TestTube2,
      isActive: pathname === "/tester",
    },
    {
      title: "Lab Admin",
      href: "/lab-admin",
      icon: FlaskConical,
      isActive: pathname === "/lab-admin",
    },
    {
      title: "Executive",
      href: "/executive",
      icon: TrendingUp,
      isActive: pathname === "/executive",
    },
  ]

  useCopilotChatSuggestions(
    {
      instructions: suggestionInstructions,
      maxSuggestions: userRole === "tester" ? 4 : 3,
      minSuggestions: 3,
    },
    [userRole, suggestionInstructions]
  )

  return (
    <div className="flex h-full flex-1">
      <Sidebar side="left" className="border-r">
        <SidebarHeader className="flex justify-between px-4 py-2">
          <div className="flex items-center gap-2">
            <LayoutDashboard className="h-6 w-6" />
            <h1 className="text-xl font-semibold tracking-tight">EnterpriseX</h1>
          </div>
        </SidebarHeader>
        <SidebarContent>
          <SidebarMenu>
            {routes.map((route) => (
              <SidebarMenuItem key={route.href} className="p-3 px-6" >
                <SidebarMenuButton asChild isActive={route.isActive}>
                  <Link href={route.href}>
                    <route.icon className="mr-2 h-5 w-5" />
                    <span>{route.title}</span>
                  </Link>
                </SidebarMenuButton>
              </SidebarMenuItem>
            ))}
          </SidebarMenu>
        </SidebarContent>
        <SidebarFooter>
          <SidebarMenu>
            <SidebarMenuItem>
              <SidebarMenuButton asChild>
                <Link href="#">
                  <Settings className="mr-2 h-5 w-5" />
                  <span>Settings</span>
                </Link>
              </SidebarMenuButton>
            </SidebarMenuItem>
            <SidebarMenuItem>
              <SidebarMenuButton asChild>
                <Link href="#">
                  <LogOut className="mr-2 h-5 w-5" />
                  <span>Logout</span>
                </Link>
              </SidebarMenuButton>
            </SidebarMenuItem>
          </SidebarMenu>
        </SidebarFooter>
      </Sidebar>
      <div className="flex flex-1 flex-col overflow-hidden">
        <header className="flex h-14 items-center gap-4 border-b bg-background px-6">
          <div className="ml-auto flex items-center gap-4">
            <span className="text-sm text-muted-foreground">Role: {displayedRole}</span>
            {/* <ModeToggle /> */}
            <Avatar>
              <AvatarImage src="/abstract-geometric-shapes.png" />
              <AvatarFallback>JD</AvatarFallback>
            </Avatar>
          </div>
        </header>
        <main className="flex-1 overflow-auto p-6">{children}</main>
      </div>
    </div>
  )
}
