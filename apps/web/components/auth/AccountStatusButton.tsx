'use client'

import { signIn, signOut } from 'next-auth/react';
import { Session } from 'next-auth';

interface AccountStatusButtonProps {
  session: Session | null;
}

export default function AccountStatusButton({ session }: AccountStatusButtonProps) {
  if (!session) {
    return (
      <button
        onClick={() => signIn()}
        className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 transition-colors"
      >
        Sign In
      </button>
    );
  }

  return (
    <div className="flex items-center gap-2">
      <div className="flex flex-col items-end">
        <span className="text-sm font-medium text-gray-900">
          {session.user?.name || session.user?.email}
        </span>
        <button
          onClick={() => signOut()}
          className="text-xs text-gray-500 hover:text-gray-700"
        >
          Sign Out
        </button>
      </div>
      {session.user?.image && (
        <img
          src={session.user.image}
          alt="Profile"
          className="w-8 h-8 rounded-full"
        />
      )}
    </div>
  );
}