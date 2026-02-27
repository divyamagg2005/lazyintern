module.exports = [
"[externals]/next/dist/compiled/next-server/app-route-turbo.runtime.dev.js [external] (next/dist/compiled/next-server/app-route-turbo.runtime.dev.js, cjs)", ((__turbopack_context__, module, exports) => {

const mod = __turbopack_context__.x("next/dist/compiled/next-server/app-route-turbo.runtime.dev.js", () => require("next/dist/compiled/next-server/app-route-turbo.runtime.dev.js"));

module.exports = mod;
}),
"[externals]/next/dist/compiled/@opentelemetry/api [external] (next/dist/compiled/@opentelemetry/api, cjs)", ((__turbopack_context__, module, exports) => {

const mod = __turbopack_context__.x("next/dist/compiled/@opentelemetry/api", () => require("next/dist/compiled/@opentelemetry/api"));

module.exports = mod;
}),
"[externals]/next/dist/compiled/next-server/app-page-turbo.runtime.dev.js [external] (next/dist/compiled/next-server/app-page-turbo.runtime.dev.js, cjs)", ((__turbopack_context__, module, exports) => {

const mod = __turbopack_context__.x("next/dist/compiled/next-server/app-page-turbo.runtime.dev.js", () => require("next/dist/compiled/next-server/app-page-turbo.runtime.dev.js"));

module.exports = mod;
}),
"[externals]/next/dist/server/app-render/work-unit-async-storage.external.js [external] (next/dist/server/app-render/work-unit-async-storage.external.js, cjs)", ((__turbopack_context__, module, exports) => {

const mod = __turbopack_context__.x("next/dist/server/app-render/work-unit-async-storage.external.js", () => require("next/dist/server/app-render/work-unit-async-storage.external.js"));

module.exports = mod;
}),
"[externals]/next/dist/server/app-render/work-async-storage.external.js [external] (next/dist/server/app-render/work-async-storage.external.js, cjs)", ((__turbopack_context__, module, exports) => {

const mod = __turbopack_context__.x("next/dist/server/app-render/work-async-storage.external.js", () => require("next/dist/server/app-render/work-async-storage.external.js"));

module.exports = mod;
}),
"[externals]/next/dist/shared/lib/no-fallback-error.external.js [external] (next/dist/shared/lib/no-fallback-error.external.js, cjs)", ((__turbopack_context__, module, exports) => {

const mod = __turbopack_context__.x("next/dist/shared/lib/no-fallback-error.external.js", () => require("next/dist/shared/lib/no-fallback-error.external.js"));

module.exports = mod;
}),
"[externals]/next/dist/server/app-render/after-task-async-storage.external.js [external] (next/dist/server/app-render/after-task-async-storage.external.js, cjs)", ((__turbopack_context__, module, exports) => {

const mod = __turbopack_context__.x("next/dist/server/app-render/after-task-async-storage.external.js", () => require("next/dist/server/app-render/after-task-async-storage.external.js"));

module.exports = mod;
}),
"[project]/app/api/dashboard/route.ts [app-route] (ecmascript)", ((__turbopack_context__) => {
"use strict";

__turbopack_context__.s([
    "GET",
    ()=>GET
]);
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$server$2e$js__$5b$app$2d$route$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/node_modules/next/server.js [app-route] (ecmascript)");
;
async function GET() {
    const mockData = {
        lastUpdated: new Date().toISOString(),
        discovery: {
            internshipsToday: 47,
            internshipsThisWeek: 312,
            tier1SuccessRate: 78.5,
            tier2SuccessRate: 92.3,
            tier3SuccessRate: 100,
            preScoreKillRate: 62.4,
            firecrawlUsed: 7,
            firecrawlLimit: 10
        },
        email: {
            regexEmails: 28,
            hunterEmails: 12,
            hunterCallsToday: 12,
            hunterDailyLimit: 15,
            validationFailuresMx: 3,
            validationFailuresFormat: 1,
            validationFailuresSmtp: 2
        },
        outreach: {
            groqDraftsGenerated: 34,
            approvalRate: 85.3,
            autoApprovals: 8,
            emailsSentToday: 11,
            dailyEmailLimit: 15,
            isWarmupPhase: true,
            warmupProgressPct: 73.3,
            pendingFollowups: 18
        },
        performance: {
            replyRate: 12.8,
            positiveReplyRate: 8.4,
            funnel: [
                {
                    label: "Discovered",
                    count: 312
                },
                {
                    label: "Pre-scored",
                    count: 117
                },
                {
                    label: "Email found",
                    count: 89
                },
                {
                    label: "Validated",
                    count: 83
                },
                {
                    label: "Full-scored",
                    count: 67
                },
                {
                    label: "Drafted",
                    count: 54
                },
                {
                    label: "Approved",
                    count: 46
                },
                {
                    label: "Sent",
                    count: 43
                },
                {
                    label: "Replied",
                    count: 5
                }
            ],
            topCompanyTypes: [
                {
                    type: "AI Startup",
                    replyRate: 14.2
                },
                {
                    type: "YC Company",
                    replyRate: 11.8
                },
                {
                    type: "Research Lab",
                    replyRate: 9.3
                }
            ]
        },
        retries: {
            activeRetriesByPhase: [
                {
                    phase: "groq",
                    activeJobs: 2
                },
                {
                    phase: "twilio",
                    activeJobs: 0
                },
                {
                    phase: "gmail",
                    activeJobs: 1
                },
                {
                    phase: "hunter",
                    activeJobs: 0
                }
            ],
            maxRetryFailures: []
        },
        scoringConfig: [
            {
                key: "relevance_score",
                weight: 0.35,
                description: "Role/title keyword match"
            },
            {
                key: "resume_overlap_score",
                weight: 0.25,
                description: "Resume keyword overlap with JD"
            },
            {
                key: "tech_stack_score",
                weight: 0.20,
                description: "Tech stack alignment"
            },
            {
                key: "location_score",
                weight: 0.10,
                description: "Location preference match"
            },
            {
                key: "historical_success_score",
                weight: 0.10,
                description: "Past reply rate for similar companies"
            }
        ]
    };
    return __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$server$2e$js__$5b$app$2d$route$5d$__$28$ecmascript$29$__["NextResponse"].json(mockData);
}
}),
];

//# sourceMappingURL=%5Broot-of-the-server%5D__1a9da224._.js.map