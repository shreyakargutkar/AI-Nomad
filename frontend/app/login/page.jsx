import { Suspense } from 'react';
import LoginForm from '@/components/auth/LoginForm';

function LoginFallback() {
  return (
    <div className="min-h-screen bg-[#FBF9F6] flex items-center justify-center">
      <div className="w-10 h-10 border-2 border-[#1E3F2E] border-t-transparent rounded-full animate-spin" />
    </div>
  );
}

export default function LoginPage() {
  return (
    <Suspense fallback={<LoginFallback />}>
      <LoginForm />
    </Suspense>
  );
}
