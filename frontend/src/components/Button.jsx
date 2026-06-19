const variants = {
  primary: "bg-teal-600 text-white hover:bg-teal-700 focus:ring-teal-500",
  secondary: "bg-white text-gray-800 ring-1 ring-gray-200 hover:bg-gray-50 focus:ring-teal-500",
  danger: "bg-rose-600 text-white hover:bg-rose-700 focus:ring-rose-500",
  ghost: "bg-transparent text-gray-700 hover:bg-gray-100 focus:ring-gray-300",
};

export default function Button({
  children,
  className = "",
  variant = "primary",
  isLoading = false,
  type = "button",
  ...props
}) {
  return (
    <button
      type={type}
      disabled={isLoading || props.disabled}
      className={`inline-flex min-h-10 items-center justify-center rounded-md px-4 py-2 text-sm font-semibold transition focus:outline-none focus:ring-2 focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-60 ${variants[variant]} ${className}`}
      {...props}
    >
      {isLoading ? "Please wait" : children}
    </button>
  );
}
