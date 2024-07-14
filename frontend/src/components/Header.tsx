import { signOut } from "auth-astro/client";
import React from "react";

export default function Header() {
  async function signOutHandler() {
    await signOut();
  }
  return (
    <nav className="relative border-b border-gray-500 ">
      <section className="container mx-auto p-4 flex justify-between">
        <h1 className="font-bold text-3xl">Dashboard</h1>
        <button
          onClick={signOutHandler}
          className="border-2 px-5 py-2 rounded-xl bg-white text-black font-medium hover:bg-black hover:text-white"
        >
          Logout
        </button>
      </section>
    </nav>
  );
}
