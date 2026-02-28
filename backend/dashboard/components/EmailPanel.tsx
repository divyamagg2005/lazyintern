interface EmailData {
  regexEmails: number;
  hunterEmails: number;
  hunterCallsToday: number;
  hunterDailyLimit: number;
  validationFailuresMx: number;
  validationFailuresFormat: number;
  validationFailuresSmtp: number;
}

export function EmailPanel({ data }: { data?: EmailData }) {
  if (!data) {
    return (
      <section className="rounded-xl border border-zinc-200 bg-white p-6 dark:border-zinc-800 dark:bg-zinc-950">
        <h2 className="text-lg font-semibold text-zinc-900 dark:text-zinc-100">
          📧 Email Extraction
        </h2>
        <p className="mt-2 text-sm text-zinc-500">Loading...</p>
      </section>
    );
  }

  const totalEmails = data.regexEmails + data.hunterEmails;
  const regexPercent = totalEmails > 0 ? (data.regexEmails / totalEmails) * 100 : 0;
  const hunterPercent = totalEmails > 0 ? (data.hunterEmails / totalEmails) * 100 : 0;
  const totalValidationFailures = data.validationFailuresMx + data.validationFailuresFormat + data.validationFailuresSmtp;

  return (
    <section className="rounded-xl border border-zinc-200 bg-white p-6 dark:border-zinc-800 dark:bg-zinc-950">
      <h2 className="text-lg font-semibold text-zinc-900 dark:text-zinc-100">
        📧 Email Extraction
      </h2>
      
      {/* Email Sources */}
      <div className="mt-4">
        <div className="flex items-center justify-between">
          <span className="text-sm text-zinc-600 dark:text-zinc-400">Total Emails</span>
          <span className="text-2xl font-bold text-zinc-900 dark:text-zinc-100">
            {totalEmails}
          </span>
        </div>
        
        <div className="mt-4 space-y-3">
          <div>
            <div className="flex items-center justify-between text-sm">
              <span className="text-zinc-600 dark:text-zinc-400">Regex (Free)</span>
              <span className="font-medium text-zinc-900 dark:text-zinc-100">
                {data.regexEmails} ({regexPercent.toFixed(0)}%)
              </span>
            </div>
            <div className="mt-1 h-2 w-full overflow-hidden rounded-full bg-zinc-200 dark:bg-zinc-800">
              <div
                className="h-full bg-green-500"
                style={{ width: `${regexPercent}%` }}
              />
            </div>
          </div>
          
          <div>
            <div className="flex items-center justify-between text-sm">
              <span className="text-zinc-600 dark:text-zinc-400">Hunter.io (Paid)</span>
              <span className="font-medium text-zinc-900 dark:text-zinc-100">
                {data.hunterEmails} ({hunterPercent.toFixed(0)}%)
              </span>
            </div>
            <div className="mt-1 h-2 w-full overflow-hidden rounded-full bg-zinc-200 dark:bg-zinc-800">
              <div
                className="h-full bg-blue-500"
                style={{ width: `${hunterPercent}%` }}
              />
            </div>
          </div>
        </div>
      </div>

      {/* Hunter Usage */}
      <div className="mt-6 rounded-lg bg-blue-50 p-4 dark:bg-blue-950/20">
        <div className="flex items-center justify-between">
          <span className="text-sm font-medium text-blue-900 dark:text-blue-100">
            Hunter API Calls Today
          </span>
          <span className="text-lg font-bold text-blue-700 dark:text-blue-400">
            {data.hunterCallsToday}/{data.hunterDailyLimit}
          </span>
        </div>
        <div className="mt-2 h-2 w-full overflow-hidden rounded-full bg-blue-200 dark:bg-blue-900">
          <div
            className="h-full bg-blue-600"
            style={{ width: `${(data.hunterCallsToday / data.hunterDailyLimit) * 100}%` }}
          />
        </div>
      </div>

      {/* Validation Failures */}
      <div className="mt-6">
        <p className="text-sm font-medium text-zinc-700 dark:text-zinc-300">
          Validation Failures ({totalValidationFailures})
        </p>
        <div className="mt-2 space-y-2">
          <div className="flex items-center justify-between text-xs">
            <span className="text-zinc-600 dark:text-zinc-400">MX Record</span>
            <span className="font-medium text-red-600 dark:text-red-400">
              {data.validationFailuresMx}
            </span>
          </div>
          <div className="flex items-center justify-between text-xs">
            <span className="text-zinc-600 dark:text-zinc-400">Format Invalid</span>
            <span className="font-medium text-red-600 dark:text-red-400">
              {data.validationFailuresFormat}
            </span>
          </div>
          <div className="flex items-center justify-between text-xs">
            <span className="text-zinc-600 dark:text-zinc-400">SMTP Ping</span>
            <span className="font-medium text-red-600 dark:text-red-400">
              {data.validationFailuresSmtp}
            </span>
          </div>
        </div>
      </div>
    </section>
  );
}

