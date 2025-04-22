import { useState, useEffect } from "react";
import { useRouter } from "next/router";
import Link from "next/link";
import Head from "next/head";
import { login, googleAuth, getApiError } from "@/lib/api";
import { saveSession, isAuthenticated } from "@/lib/auth";
import { Spinner } from "@/components/ui/Spinner";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (isAuthenticated()) router.replace("/dashboard");
  }, [router]);

  // Handle Google OAuth callback code
  useEffect(() => {
    const { code } = router.query;
    if (typeof code === "string") {
      setLoading(true);
      googleAuth(code)
        .then((auth) => {
          saveSession(auth);
          router.replace("/dashboard");
        })
        .catch((err) => {
          setError(getApiError(err));
          setLoading(false);
        });
    }
  }, [router.query, router]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const auth = await login(email, password);
      saveSession(auth);
      router.push("/dashboard");
    } catch (err) {
      setError(getApiError(err));
    } finally {
      setLoading(false);
    }
  };

  const handleGoogle = () => {
    const params = new URLSearchParams({
      client_id: process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID ?? "",
      redirect_uri: `${window.location.origin}/auth/login`,
      response_type: "code",
      scope: "openid email profile",
      access_type: "offline",
    });
    window.location.href = `https://accounts.google.com/o/oauth2/v2/auth?${params}`;
  };

  return (
    <>
      <Head>
        <title>Sign in — QuarterWatch</title>
      </Head>

      <div className="min-h-screen bg-stone-25 flex items-center justify-center px-4">
        <div className="w-full max-w-sm animate-in">
          {/* Logo */}
          <div className="flex items-center gap-2.5 justify-center mb-10">
            <div className="w-8 h-8 rounded-lg bg-stone-900 flex items-center justify-center">
              <span className="text-amber-400 text-sm font-bold font-mono">Q</span>
            </div>
            <span className="font-display font-semibold text-stone-900 text-lg">
              QuarterWatch
            </span>
          </div>

          <div className="card p-8">
            <h1 className="font-display text-2xl font-semibold text-stone-900 mb-1">
              Welcome back
            </h1>
            <p className="text-stone-500 text-sm mb-7">
              Sign in to your account to continue.
            </p>

            {/* Google OAuth */}
            <button
              onClick={handleGoogle}
              disabled={loading}
              className="btn-secondary w-full mb-5 gap-3"
            >
              <svg width="18" height="18" viewBox="0 0 18 18" fill="none">
                <path d="M17.64 9.205c0-.639-.057-1.252-.164-1.841H9v3.481h4.844a4.14 4.14 0 01-1.796 2.716v2.259h2.908c1.702-1.567 2.684-3.875 2.684-6.615z" fill="#4285F4"/>
                <path d="M9 18c2.43 0 4.467-.806 5.956-2.18l-2.908-2.259c-.806.54-1.837.86-3.048.86-2.344 0-4.328-1.584-5.036-3.711H.957v2.332A8.997 8.997 0 009 18z" fill="#34A853"/>
                <path d="M3.964 10.71A5.41 5.41 0 013.682 9c0-.593.102-1.17.282-1.71V4.958H.957A8.996 8.996 0 000 9c0 1.452.348 2.827.957 4.042l3.007-2.332z" fill="#FBBC05"/>
                <path d="M9 3.58c1.321 0 2.508.454 3.44 1.345l2.582-2.58C13.463.891 11.426 0 9 0A8.997 8.997 0 00.957 4.958L3.964 7.29C4.672 5.163 6.656 3.58 9 3.58z" fill="#EA4335"/>
              </svg>
              Continue with Google
            </button>

            <div className="flex items-center gap-3 mb-5">
              <div className="flex-1 h-px bg-stone-100" />
              <span className="text-stone-400 text-xs">or</span>
              <div className="flex-1 h-px bg-stone-100" />
            </div>

            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-stone-700 mb-1.5">
                  Email
                </label>
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="you@company.com"
                  required
                  autoComplete="email"
                  className="input-base"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-stone-700 mb-1.5">
                  Password
                </label>
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••"
                  required
                  autoComplete="current-password"
                  className="input-base"
                />
              </div>

              {error && (
                <p className="text-sm text-red-600 bg-red-50 border border-red-100 rounded-lg px-3 py-2">
                  {error}
                </p>
              )}

              <button
                type="submit"
                disabled={loading}
                className="btn-primary w-full mt-1"
              >
                {loading ? <Spinner size="sm" /> : "Sign in"}
              </button>
            </form>
          </div>

          <p className="text-center text-sm text-stone-500 mt-5">
            No account?{" "}
            <Link
              href="/auth/register"
              className="text-stone-800 font-medium hover:text-amber-600 transition-colors"
            >
              Create one
            </Link>
          </p>
        </div>
      </div>
    </>
  );
}
