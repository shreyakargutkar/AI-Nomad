import { redirect } from 'next/navigation';

/** Alfred lives in the floating chat widget — no standalone voice page. */
export default function ChatbotRedirect() {
  redirect('/');
}
