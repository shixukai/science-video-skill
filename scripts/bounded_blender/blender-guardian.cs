// Reviewed local diagnostic launcher only. This file is source; no compilation or execution
// was performed while preparing it. Official API references:
// https://learn.microsoft.com/en-us/windows/win32/api/processthreadsapi/nf-processthreadsapi-updateprocthreadattribute
// https://learn.microsoft.com/en-us/windows/win32/api/winnt/ns-winnt-jobobject_basic_limit_information
// https://learn.microsoft.com/en-us/windows/win32/api/winnt/ns-winnt-jobobject_associate_completion_port
// https://devblogs.microsoft.com/oldnewthing/20230209-00/?p=107812/
using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Diagnostics;
using System.Globalization;
using System.IO;
using System.Runtime.InteropServices;
using System.Security.Cryptography;
using System.Text;
using System.Threading;

namespace ReviewedBlenderLocal
{
    public sealed class GuardianResult
    {
        public string Status = "unknown_requires_reconciliation";
        public string Error;
        public uint PID;
        public string ExecutablePath;
        public string CreationTimeUTC;
        public long CreationFileTime;
        public bool ProcessCreated;
        public bool IdentityVerified;
        public bool Resumed;
        public bool RootExited;
        public bool TreeExitVerified;
        public string TreeExitEvidence;
        public bool TimedOut;
        public bool LimitBreach;
        public bool JobCloseAttempted;
        public bool JobCloseCompleted;
        public bool JobCloseSucceeded;
        public bool CleanupAttempted;
        public int JobCloseWin32Error;
        public string JobCloseReason;
        public double JobCloseAtSeconds;
        public uint? ExitCode;
        public double ElapsedSeconds;
        public string StartedUTC;
        public string FinishedUTC;
        public string NativeOutcomeWriteError;
        public bool JobCloseReceiptPending;
    }

    public static class Guardian
    {
        static string Root;
        static int InvocationClaimed;
        const int CutoffMilliseconds = 295000;
        const int MaximumMilliseconds = 300000;
        const uint WAIT_OBJECT_0 = 0, WAIT_TIMEOUT = 258, WAIT_FAILED = 0xffffffff;
        const uint CREATE_SUSPENDED = 4, CREATE_NO_WINDOW = 0x08000000, EXTENDED_STARTUPINFO_PRESENT = 0x00080000;
        const uint STARTF_USESHOWWINDOW = 1, STARTF_USESTDHANDLES = 0x100;
        const uint JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE = 0x2000;
        static readonly IntPtr Invalid = new IntPtr(-1);

        [StructLayout(LayoutKind.Sequential)] struct SECURITY_ATTRIBUTES { public int nLength; public IntPtr lpSecurityDescriptor; [MarshalAs(UnmanagedType.Bool)] public bool bInheritHandle; }
        [StructLayout(LayoutKind.Sequential, CharSet = CharSet.Unicode)] struct STARTUPINFO
        {
            public uint cb; public string lpReserved, lpDesktop, lpTitle;
            public uint dwX, dwY, dwXSize, dwYSize, dwXCountChars, dwYCountChars, dwFillAttribute, dwFlags;
            public ushort wShowWindow, cbReserved2;
            public IntPtr lpReserved2, hStdInput, hStdOutput, hStdError;
        }
        [StructLayout(LayoutKind.Sequential)] struct STARTUPINFOEX { public STARTUPINFO StartupInfo; public IntPtr lpAttributeList; }
        [StructLayout(LayoutKind.Sequential)] struct PROCESS_INFORMATION { public IntPtr hProcess, hThread; public uint dwProcessId, dwThreadId; }
        [StructLayout(LayoutKind.Sequential)] struct BASIC_LIMIT
        {
            public long PerProcessUserTimeLimit, PerJobUserTimeLimit; public uint LimitFlags;
            public UIntPtr MinimumWorkingSetSize, MaximumWorkingSetSize; public uint ActiveProcessLimit;
            public UIntPtr Affinity; public uint PriorityClass, SchedulingClass;
        }
        [StructLayout(LayoutKind.Sequential)] struct IO_COUNTERS { public ulong ReadOperationCount, WriteOperationCount, OtherOperationCount, ReadTransferCount, WriteTransferCount, OtherTransferCount; }
        [StructLayout(LayoutKind.Sequential)] struct EXTENDED_LIMIT
        {
            public BASIC_LIMIT BasicLimitInformation; public IO_COUNTERS IoInfo;
            public UIntPtr ProcessMemoryLimit, JobMemoryLimit, PeakProcessMemoryUsed, PeakJobMemoryUsed;
        }
        [StructLayout(LayoutKind.Sequential)] struct ACCOUNTING
        {
            public long TotalUserTime, TotalKernelTime, ThisPeriodTotalUserTime, ThisPeriodTotalKernelTime;
            public uint TotalPageFaultCount, TotalProcesses, ActiveProcesses, TotalTerminatedProcesses;
        }
        [StructLayout(LayoutKind.Sequential)] struct COMPLETION_ASSOCIATION { public IntPtr CompletionKey, CompletionPort; }

        [DllImport("kernel32.dll", CharSet = CharSet.Unicode, ExactSpelling = true, SetLastError = true)] static extern IntPtr CreateJobObjectW(IntPtr attributes, string name);
        [DllImport("kernel32.dll", SetLastError = true)] [return: MarshalAs(UnmanagedType.Bool)] static extern bool SetInformationJobObject(IntPtr job, int infoClass, IntPtr info, uint length);
        [DllImport("kernel32.dll", SetLastError = true)] [return: MarshalAs(UnmanagedType.Bool)] static extern bool QueryInformationJobObject(IntPtr job, int infoClass, out ACCOUNTING info, uint length, IntPtr returnLength);
        [DllImport("kernel32.dll", SetLastError = true)] [return: MarshalAs(UnmanagedType.Bool)] static extern bool IsProcessInJob(IntPtr process, IntPtr job, [MarshalAs(UnmanagedType.Bool)] out bool result);
        [DllImport("kernel32.dll", CharSet = CharSet.Unicode, ExactSpelling = true, SetLastError = true)] static extern IntPtr CreateFileW(string name, uint access, uint share, ref SECURITY_ATTRIBUTES attributes, uint disposition, uint flags, IntPtr template);
        [DllImport("kernel32.dll", SetLastError = true)] [return: MarshalAs(UnmanagedType.Bool)] static extern bool InitializeProcThreadAttributeList(IntPtr list, int count, uint flags, ref UIntPtr size);
        [DllImport("kernel32.dll", SetLastError = true)] [return: MarshalAs(UnmanagedType.Bool)] static extern bool UpdateProcThreadAttribute(IntPtr list, uint flags, UIntPtr attribute, IntPtr value, UIntPtr size, IntPtr previous, IntPtr returnSize);
        [DllImport("kernel32.dll")] static extern void DeleteProcThreadAttributeList(IntPtr list);
        [DllImport("kernel32.dll", CharSet = CharSet.Unicode, ExactSpelling = true, SetLastError = true)] [return: MarshalAs(UnmanagedType.Bool)] static extern bool CreateProcessW(string application, StringBuilder commandLine, IntPtr processAttributes, IntPtr threadAttributes, [MarshalAs(UnmanagedType.Bool)] bool inheritHandles, uint flags, IntPtr environment, string directory, ref STARTUPINFOEX startup, out PROCESS_INFORMATION process);
        [DllImport("kernel32.dll", CharSet = CharSet.Unicode, ExactSpelling = true, SetLastError = true)] [return: MarshalAs(UnmanagedType.Bool)] static extern bool QueryFullProcessImageNameW(IntPtr process, uint flags, StringBuilder name, ref uint size);
        [DllImport("kernel32.dll", SetLastError = true)] [return: MarshalAs(UnmanagedType.Bool)] static extern bool GetProcessTimes(IntPtr process, out long creation, out long exit, out long kernel, out long user);
        [DllImport("kernel32.dll", SetLastError = true)] static extern uint GetProcessId(IntPtr process);
        [DllImport("kernel32.dll", SetLastError = true)] static extern uint ResumeThread(IntPtr thread);
        [DllImport("kernel32.dll", SetLastError = true)] static extern uint WaitForSingleObject(IntPtr handle, uint milliseconds);
        [DllImport("kernel32.dll", SetLastError = true)] [return: MarshalAs(UnmanagedType.Bool)] static extern bool GetExitCodeProcess(IntPtr process, out uint code);
        [DllImport("kernel32.dll", SetLastError = true)] [return: MarshalAs(UnmanagedType.Bool)] static extern bool CloseHandle(IntPtr handle);
        [DllImport("kernel32.dll", SetLastError = true)] static extern IntPtr CreateIoCompletionPort(IntPtr file, IntPtr existing, UIntPtr key, uint threads);
        [DllImport("kernel32.dll", SetLastError = true)] [return: MarshalAs(UnmanagedType.Bool)] static extern bool GetQueuedCompletionStatus(IntPtr port, out uint message, out UIntPtr key, out IntPtr value, uint milliseconds);

        static Win32Exception Failure(string action) { int code = Marshal.GetLastWin32Error(); return new Win32Exception(code, action + ": " + new Win32Exception(code).Message); }
        static void Need(bool ok, string why) { if (!ok) throw new InvalidOperationException(why); }
        static string SHA(string path) { using (var s = File.OpenRead(path)) using (var h = SHA256.Create()) { return BitConverter.ToString(h.ComputeHash(s)).Replace("-", "").ToLowerInvariant(); } }
        static string J(string value)
        {
            if (value == null) return "null";
            var b = new StringBuilder("\"");
            foreach (char c in value) { if (c == '"' || c == '\\') { b.Append('\\'); b.Append(c); } else if (c < 32) b.Append("\\u" + ((int)c).ToString("x4")); else b.Append(c); }
            return b.Append('"').ToString();
        }
        static string B(bool value) { return value ? "true" : "false"; }
        static string N(double value) { return value.ToString("R", CultureInfo.InvariantCulture); }
        static void WriteNew(string name, string json)
        {
            byte[] bytes = new UTF8Encoding(false).GetBytes(json + "\n");
            using (var stream = new FileStream(Path.Combine(Root, name), FileMode.CreateNew, FileAccess.Write, FileShare.Read)) { stream.Write(bytes, 0, bytes.Length); stream.Flush(true); }
        }
        static void AddError(GuardianResult r, string text) { r.Error = String.IsNullOrEmpty(r.Error) ? text : r.Error + " | " + text; }
        static void SetInfo<T>(IntPtr job, int infoClass, T value) where T : struct
        {
            int size = Marshal.SizeOf(typeof(T)); IntPtr p = Marshal.AllocHGlobal(size);
            try { Marshal.StructureToPtr(value, p, false); if (!SetInformationJobObject(job, infoClass, p, (uint)size)) throw Failure("SetInformationJobObject " + infoClass); }
            finally { Marshal.FreeHGlobal(p); }
        }

        // There is exactly one owned job handle, it is never inheritable or duplicated.
        // Exchange arbitrates normal completion, exceptional completion and watchdog.
        sealed class OwnedJob
        {
            IntPtr handle;
            public readonly ManualResetEvent CloseDone = new ManualResetEvent(false);
            public int CloseClaimed;
            public volatile bool CloseCompleted, CloseSucceeded, CleanupAttempted, Deadline, ReceiptCompleted;
            public int CloseError;
            public string CloseReason, ReceiptError;
            public double CloseAtSeconds;
            readonly Stopwatch clock;
            public OwnedJob(IntPtr value, Stopwatch timer) { handle = value; clock = timer; }
            public IntPtr Handle { get { return Interlocked.CompareExchange(ref handle, IntPtr.Zero, IntPtr.Zero); } }
            public void CloseOnce(string reason, bool cleanup, bool deadline)
            {
                if (Interlocked.CompareExchange(ref CloseClaimed, 1, 0) != 0) return;
                CleanupAttempted = cleanup; Deadline = deadline; CloseReason = reason; CloseAtSeconds = clock.Elapsed.TotalSeconds;
                IntPtr h = Interlocked.Exchange(ref handle, IntPtr.Zero);
                try
                {
                    CloseSucceeded = h != IntPtr.Zero && CloseHandle(h);
                    if (!CloseSucceeded) CloseError = Marshal.GetLastWin32Error();
                }
                finally
                {
                    CloseCompleted = true; CloseDone.Set();
                    try { WriteNew("render-job-close.json", "{\"Reason\":" + J(reason) + ",\"CleanupAttempted\":" + B(cleanup) + ",\"DeadlineTriggered\":" + B(deadline) + ",\"AtSeconds\":" + N(CloseAtSeconds) + ",\"CloseHandleSucceeded\":" + B(CloseSucceeded) + ",\"Win32Error\":" + CloseError + ",\"CloseAttempts\":1,\"Scope\":\"only_new_anonymous_job_and_its_members\"}"); }
                    catch (Exception e) { ReceiptError = e.Message; }
                    finally { ReceiptCompleted = true; }
                }
            }
        }

        static bool ObserveTree(IntPtr port, GuardianResult result, uint wait)
        {
            uint message; UIntPtr key; IntPtr value;
            bool ok = GetQueuedCompletionStatus(port, out message, out key, out value, wait);
            if (!ok)
            {
                int code = Marshal.GetLastWin32Error();
                if (code != (int)WAIT_TIMEOUT) throw new Win32Exception(code, "Owned job completion port query");
                return false;
            }
            if (key.ToUInt64() == 1 && message == 4) { result.TreeExitVerified = true; result.TreeExitEvidence = "private_job_ACTIVE_PROCESS_ZERO_completion"; return true; }
            return false;
        }
        static void ObserveRoot(IntPtr process, GuardianResult r)
        {
            uint state = WaitForSingleObject(process, 0);
            if (state == WAIT_FAILED) throw Failure("WaitForSingleObject owned root");
            if (state == WAIT_OBJECT_0) { r.RootExited = true; uint code; if (!GetExitCodeProcess(process, out code)) throw Failure("GetExitCodeProcess"); r.ExitCode = code; }
        }
        static void Monitor(IntPtr process, IntPtr port, OwnedJob job, Stopwatch clock, GuardianResult r)
        {
            while (clock.ElapsedMilliseconds < MaximumMilliseconds)
            {
                ObserveRoot(process, r);
                if (r.RootExited && r.TreeExitVerified) return;
                if (clock.ElapsedMilliseconds >= CutoffMilliseconds) job.CloseOnce("wall_clock_295_seconds", true, true);
                int remaining = MaximumMilliseconds - (int)Math.Min(clock.ElapsedMilliseconds, MaximumMilliseconds);
                if (remaining <= 0) break;
                ObserveTree(port, r, (uint)Math.Min(50, remaining));
            }
            ObserveRoot(process, r);
            // No unbounded wait and no second cleanup attempt after the deadline.
            r.LimitBreach = !r.RootExited || !r.TreeExitVerified;
        }

        public static GuardianResult Run(string taskRoot, string executable, string[] arguments, string directory, int parentLauncherPID, string executableSHA256, string skillRoot, string skillLock, string profile)
        {
            // One invocation per process: no mutable shared root can race a prior watchdog.
            Need(Interlocked.CompareExchange(ref InvocationClaimed, 1, 0) == 0, "Guardian already invoked; reconcile instead of retry");
            Root = Path.GetFullPath(taskRoot);
            string Exe = Path.GetFullPath(executable);
            string ExeSHA = executableSHA256;
            var r = new GuardianResult { StartedUTC = DateTime.UtcNow.ToString("o") };
            var clock = new Stopwatch(); OwnedJob job = null; Thread watcher = null;
            var cancelWatchdog = new ManualResetEvent(false);
            PROCESS_INFORMATION pi = new PROCESS_INFORMATION();
            IntPtr stdout = IntPtr.Zero, stderr = IntPtr.Zero, stdin = IntPtr.Zero, attributes = IntPtr.Zero, handleValues = IntPtr.Zero, jobValue = IntPtr.Zero, port = IntPtr.Zero;
            bool attributesInitialized = false, watcherStarted = false;
            try
            {
                Need(IntPtr.Size == 8 && Environment.OSVersion.Platform == PlatformID.Win32NT && Environment.OSVersion.Version.Major >= 10, "64-bit Windows 10+ is required; no fallback launch");
                string package = Path.Combine(Root, "package");
                Need(profile == "blender-local-three-keyframes" || profile == "blender-local-bounded-reveal", "Unsupported fixed render profile");
                string script = Path.Combine(package, profile == "blender-local-three-keyframes" ? "run_three_keyframes.py" : "run_bounded_reveal.py");
                string[] expected = { "--background", "--factory-startup", "--disable-autoexec", "--threads", "2", "--python-exit-code", "1", "--python", script, "--", "--skill-root", skillRoot, "--skill-lock", skillLock };
                Need(String.Equals(Path.GetFullPath(taskRoot), Root, StringComparison.OrdinalIgnoreCase) && String.Equals(Path.GetFullPath(executable), Exe, StringComparison.OrdinalIgnoreCase) && String.Equals(Path.GetFullPath(directory), package, StringComparison.OrdinalIgnoreCase), "Frozen absolute invocation paths required");
                Need(arguments != null && arguments.Length == expected.Length, "Frozen argument vector required");
                for (int i = 0; i < expected.Length; i++) Need(arguments[i] == expected[i], "Frozen argument mismatch at " + i);
                Need(SHA(Exe) == ExeSHA && !Directory.Exists(Path.Combine(package, "output")), "Executable changed or output already exists");
                foreach (string name in new[] { "render-process.json", "render-native-outcome.json", "render-job-close.json", "render-stdout.log", "render-stderr.log" }) Need(!File.Exists(Path.Combine(Root, name)), "Prior execution evidence exists: " + name);

                IntPtr nativeJob = CreateJobObjectW(IntPtr.Zero, null);
                if (nativeJob == IntPtr.Zero) throw Failure("CreateJobObjectW private anonymous job");
                job = new OwnedJob(nativeJob, clock);
                var limits = new EXTENDED_LIMIT(); limits.BasicLimitInformation.LimitFlags = JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE;
                SetInfo(nativeJob, 9, limits);
                port = CreateIoCompletionPort(Invalid, IntPtr.Zero, UIntPtr.Zero, 1);
                if (port == IntPtr.Zero) throw Failure("CreateIoCompletionPort private observer");
                SetInfo(nativeJob, 7, new COMPLETION_ASSOCIATION { CompletionKey = new IntPtr(1), CompletionPort = port });

                var sa = new SECURITY_ATTRIBUTES { nLength = Marshal.SizeOf(typeof(SECURITY_ATTRIBUTES)), lpSecurityDescriptor = IntPtr.Zero, bInheritHandle = true };
                stdout = CreateFileW(Path.Combine(Root, "render-stdout.log"), 0x40000000, 1, ref sa, 1, 0x80, IntPtr.Zero);
                if (stdout == Invalid) throw Failure("CreateNew stdout log");
                stderr = CreateFileW(Path.Combine(Root, "render-stderr.log"), 0x40000000, 1, ref sa, 1, 0x80, IntPtr.Zero);
                if (stderr == Invalid) throw Failure("CreateNew stderr log");
                stdin = CreateFileW("NUL", 0x80000000, 3, ref sa, 3, 0x80, IntPtr.Zero);
                if (stdin == Invalid) throw Failure("Open NUL stdin");

                UIntPtr length = UIntPtr.Zero;
                InitializeProcThreadAttributeList(IntPtr.Zero, 2, 0, ref length);
                Need(length.ToUInt64() > 0 && length.ToUInt64() <= 1048576, "Unexpected native attribute size");
                attributes = Marshal.AllocHGlobal(checked((int)length.ToUInt64()));
                if (!InitializeProcThreadAttributeList(attributes, 2, 0, ref length)) throw Failure("InitializeProcThreadAttributeList");
                attributesInitialized = true;
                handleValues = Marshal.AllocHGlobal(3 * IntPtr.Size);
                Marshal.WriteIntPtr(handleValues, 0, stdin); Marshal.WriteIntPtr(handleValues, IntPtr.Size, stdout); Marshal.WriteIntPtr(handleValues, 2 * IntPtr.Size, stderr);
                if (!UpdateProcThreadAttribute(attributes, 0, new UIntPtr(0x20002), handleValues, new UIntPtr((uint)(3 * IntPtr.Size)), IntPtr.Zero, IntPtr.Zero)) throw Failure("Explicit three-handle inheritance list");
                jobValue = Marshal.AllocHGlobal(IntPtr.Size); Marshal.WriteIntPtr(jobValue, nativeJob);
                if (!UpdateProcThreadAttribute(attributes, 0, new UIntPtr(0x2000D), jobValue, new UIntPtr((uint)IntPtr.Size), IntPtr.Zero, IntPtr.Zero)) throw Failure("Atomic private job assignment; no fallback");

                var si = new STARTUPINFOEX(); si.StartupInfo.cb = (uint)Marshal.SizeOf(typeof(STARTUPINFOEX));
                si.StartupInfo.dwFlags = STARTF_USESHOWWINDOW | STARTF_USESTDHANDLES; si.StartupInfo.wShowWindow = 0;
                si.StartupInfo.hStdInput = stdin; si.StartupInfo.hStdOutput = stdout; si.StartupInfo.hStdError = stderr; si.lpAttributeList = attributes;
                // All frozen arguments contain no quotes; quote each independently.
                var command = new StringBuilder("\"" + Exe + "\"");
                foreach (string arg in arguments) { Need(arg.IndexOf('"') < 0 && !arg.EndsWith("\\", StringComparison.Ordinal), "Unsupported frozen argument quoting"); command.Append(" \"").Append(arg).Append('"'); }
                clock.Start();
                if (!CreateProcessW(Exe, command, IntPtr.Zero, IntPtr.Zero, true, CREATE_SUSPENDED | CREATE_NO_WINDOW | EXTENDED_STARTUPINFO_PRESENT, IntPtr.Zero, package, ref si, out pi)) throw Failure("CreateProcessW suspended atomic-job launch");
                r.ProcessCreated = true; r.PID = pi.dwProcessId;
                // The sole newly-created root is already in our private job and is
                // still suspended. Watchdog is independent of PowerShell and file I/O.
                watcher = new Thread(delegate()
                {
                    int wait = Math.Max(0, CutoffMilliseconds - (int)Math.Min(clock.ElapsedMilliseconds, CutoffMilliseconds));
                    if (!cancelWatchdog.WaitOne(wait)) job.CloseOnce("wall_clock_295_seconds", true, true);
                });
                watcher.IsBackground = true; watcher.Name = "reviewed-local-job-295-second-watchdog"; watcher.Start(); watcherStarted = true;

                uint capacity = 32768; var image = new StringBuilder((int)capacity);
                if (!QueryFullProcessImageNameW(pi.hProcess, 0, image, ref capacity)) throw Failure("Held-handle image identity");
                r.ExecutablePath = image.ToString();
                long creation, exit, kernel, user;
                if (!GetProcessTimes(pi.hProcess, out creation, out exit, out kernel, out user)) throw Failure("Held-handle creation time");
                r.CreationFileTime = creation; r.CreationTimeUTC = DateTime.FromFileTimeUtc(creation).ToString("o");
                Need(GetProcessId(pi.hProcess) == pi.dwProcessId && String.Equals(r.ExecutablePath, Exe, StringComparison.OrdinalIgnoreCase) && creation > 0, "Held process PID/path/creation identity mismatch");
                // JOB_LIST made membership atomic inside CreateProcessW. Do not
                // query a raw Job handle while the watchdog may close that handle.
                r.IdentityVerified = true;
                string argsJson = "[" + String.Join(",", Array.ConvertAll(arguments, new Converter<string, string>(J))) + "]";
                WriteNew("render-process.json", "{\"Status\":\"started_verified\",\"StartedUTC\":" + J(DateTime.UtcNow.ToString("o")) + ",\"PID\":" + r.PID + ",\"ExecutablePath\":" + J(r.ExecutablePath) + ",\"CreationTimeUTC\":" + J(r.CreationTimeUTC) + ",\"CreationFileTime\":" + creation + ",\"ExpectedArguments\":" + argsJson + ",\"ParentLauncherPID\":" + parentLauncherPID + ",\"IdentityFromHeldNativeHandle\":true,\"AtomicPrivateJobAssignment\":true,\"JobHandleInherited\":false,\"InheritedHandleCount\":3,\"ResumePending\":true}");
                Need(job.CloseClaimed == 0 && clock.ElapsedMilliseconds < CutoffMilliseconds, "Deadline reached before resume");
                uint previous = ResumeThread(pi.hThread);
                if (previous == 0xffffffff) throw Failure("ResumeThread owned root");
                Need(previous == 1, "Unexpected initial suspend count: " + previous); r.Resumed = true;
                Monitor(pi.hProcess, port, job, clock, r);
            }
            catch (Exception e)
            {
                AddError(r, e.GetType().Name + ": " + e.Message);
                if (job != null) job.CloseOnce(r.ProcessCreated ? "exception_owned_job_cleanup" : "setup_failed_empty_job_release", r.ProcessCreated, false);
                if (r.ProcessCreated && port != IntPtr.Zero)
                {
                    try { Monitor(pi.hProcess, port, job, clock, r); }
                    catch (Exception observeError) { AddError(r, "Bounded reconciliation: " + observeError.Message); }
                }
            }
            finally
            {
                cancelWatchdog.Set();
                if (job != null) job.CloseOnce(r.RootExited && r.TreeExitVerified ? "completed_empty_job_release" : "final_owned_job_cleanup", r.ProcessCreated && !(r.RootExited && r.TreeExitVerified), false);
                if (watcherStarted)
                {
                    try { watcher.Join(Math.Max(0, Math.Min(100, MaximumMilliseconds - (int)Math.Min(clock.ElapsedMilliseconds, MaximumMilliseconds)))); }
                    catch (Exception e) { AddError(r, "Watchdog join: " + e.Message); }
                }
                if (job != null)
                {
                    r.JobCloseAttempted = job.CloseClaimed != 0; r.JobCloseCompleted = job.CloseCompleted; r.JobCloseSucceeded = job.CloseSucceeded;
                    r.CleanupAttempted = job.CleanupAttempted; r.TimedOut = job.Deadline; r.JobCloseReason = job.CloseReason; r.JobCloseAtSeconds = job.CloseAtSeconds; r.JobCloseWin32Error = job.CloseError;
                    r.JobCloseReceiptPending = !job.ReceiptCompleted;
                    if (!String.IsNullOrEmpty(job.ReceiptError)) AddError(r, "Job close receipt: " + job.ReceiptError);
                }
                if (attributesInitialized) DeleteProcThreadAttributeList(attributes);
                foreach (IntPtr p in new[] { attributes, handleValues, jobValue }) if (p != IntPtr.Zero) Marshal.FreeHGlobal(p);
                foreach (IntPtr h in new[] { pi.hThread, pi.hProcess, stdin, stdout, stderr, port })
                    if (h != IntPtr.Zero && h != Invalid && !CloseHandle(h)) AddError(r, "Non-job handle release failed with Win32 error " + Marshal.GetLastWin32Error());
                clock.Stop(); r.ElapsedSeconds = clock.Elapsed.TotalSeconds; r.FinishedUTC = DateTime.UtcNow.ToString("o");
                r.LimitBreach = r.LimitBreach || r.ElapsedSeconds > 300;
                if (!r.ProcessCreated) r.Status = "failed_to_start";
                else if (!r.RootExited || !r.TreeExitVerified || !r.JobCloseCompleted || !r.JobCloseSucceeded) r.Status = "unknown_requires_reconciliation";
                else if (r.TimedOut || r.LimitBreach) r.Status = "timed_out";
                else if (!String.IsNullOrEmpty(r.Error) || !r.IdentityVerified || !r.Resumed) r.Status = "failed_guardian_or_identity";
                else r.Status = r.ExitCode == 0 ? "exited_zero_unverified" : "failed_exit";
                try
                {
                    WriteNew("render-native-outcome.json", "{\"Status\":" + J(r.Status) + ",\"PID\":" + r.PID + ",\"ExecutablePath\":" + J(r.ExecutablePath) + ",\"CreationTimeUTC\":" + J(r.CreationTimeUTC) + ",\"ProcessCreated\":" + B(r.ProcessCreated) + ",\"IdentityVerified\":" + B(r.IdentityVerified) + ",\"Resumed\":" + B(r.Resumed) + ",\"RootExited\":" + B(r.RootExited) + ",\"TreeExitVerified\":" + B(r.TreeExitVerified) + ",\"TreeExitEvidence\":" + J(r.TreeExitEvidence) + ",\"ExitCode\":" + (r.ExitCode.HasValue ? r.ExitCode.Value.ToString(CultureInfo.InvariantCulture) : "null") + ",\"ElapsedSeconds\":" + N(r.ElapsedSeconds) + ",\"TimedOut\":" + B(r.TimedOut) + ",\"LimitBreach\":" + B(r.LimitBreach) + ",\"JobCloseAttempted\":" + B(r.JobCloseAttempted) + ",\"JobCloseCompleted\":" + B(r.JobCloseCompleted) + ",\"JobCloseSucceeded\":" + B(r.JobCloseSucceeded) + ",\"JobCloseReason\":" + J(r.JobCloseReason) + ",\"JobCloseAtSeconds\":" + N(r.JobCloseAtSeconds) + ",\"JobCloseWin32Error\":" + r.JobCloseWin32Error + ",\"CleanupAttempted\":" + B(r.CleanupAttempted) + ",\"MaximumSeconds\":300,\"WatchdogSeconds\":295,\"Error\":" + J(r.Error) + ",\"VisualAccepted\":false,\"FullVideoAuthorized\":false}");
                }
                catch (Exception e) { r.NativeOutcomeWriteError = e.Message; AddError(r, "Native outcome write: " + e.Message); }
                // These are local managed wait handles, not process/job handles.
                // Keep them alive if the watchdog is still unwinding at deadline.
                if (!watcherStarted || !watcher.IsAlive) { cancelWatchdog.Dispose(); if (job != null) job.CloseDone.Dispose(); }
            }
            return r;
        }
    }
}
