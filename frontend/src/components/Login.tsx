import React, { useEffect, useState } from "react";
import { signIn, signOut } from "auth-astro/client";

interface Props {
  errorMessage: string;
}

export default function Login(props: Props) {
  const [formData, setFormData] = useState<{
    emailOrUsername: string;
    password: string;
  }>({
    emailOrUsername: "",
    password: "",
  });
  const authHandler = async () => {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/;
    if (emailRegex.test(formData.emailOrUsername)) {
      try {
        await signIn("credentials", {
          email: formData.emailOrUsername,
          password: formData.password,
          callbackUrl: "/",
          redirect: true,
        });
      } catch (e) {
        console.error(e);
      }
    } else {
      try {
        await signIn("credentials", {
          username: formData.emailOrUsername,
          password: formData.password,
          callbackUrl: "/dashboard",
          redirect: true,
        });
      } catch (e) {
        console.error(e);
      }
    }
  };
  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prevState) => ({
      ...prevState,
      [name]: value,
    }));
  };
  useEffect(() => {
    console.log(formData);
  }, [formData]);
  useEffect(() => {});
  return (
    <div className="w-full max-w-sm mx-auto overflow-hidden bg-black border-white border rounded-lg shadow-md ">
      <div className="px-6 py-4">
        <div className="flex justify-center mx-auto">
          <img
            className="w-auto h-7 sm:h-12"
            src="https://static.vecteezy.com/system/resources/previews/021/608/790/original/chatgpt-logo-chat-gpt-icon-on-black-background-free-vector.jpg"
            alt=""
          />
        </div>

        <h3 className="mt-3 text-xl font-medium text-center text-gray-200 ">
          Welcome Back
        </h3>

        <p className="mt-1 text-center text-gray-100 ">
          Login as Administrator
        </p>

        <form>
          <div className="w-full mt-4">
            <input
              className="block w-full px-4 py-2 mt-2 text-gray-700 placeholder-gray-100 bg-black border rounded-lg "
              type="text"
              name="emailOrUsername"
              placeholder="Email or Username"
              onChange={handleChange}
              value={formData.emailOrUsername}
            />
          </div>

          <div className="w-full mt-4">
            <input
              className="block w-full px-4 py-2 mt-2 text-gray-700 placeholder-gray-100 bg-black border rounded-lg "
              type="password"
              name="password"
              onChange={handleChange}
              value={formData.password}
              placeholder="Password"
              aria-label="Password"
            />
          </div>

          <div className="flex items-center justify-center mt-4">
            <button
              type="button"
              onClick={authHandler}
              className="px-6 py-2 text-sm font-medium tracking-wide text-white border capitalize transition-colors duration-300 transform bg-black rounded-lg hover:bg-white hover:text-black focus:outline-none focus:ring focus:ring-white focus:ring-opacity-50"
            >
              Sign In
            </button>
          </div>
          {props.errorMessage ? (
            <div>
              <p className="text-red-100 text-xs italic mt-2 text-center">
                {props.errorMessage}
              </p>
            </div>
          ) : (
            <></>
          )}
        </form>
      </div>
    </div>
  );
}
