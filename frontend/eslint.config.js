// Track 20.9 · Real ESLint 9 flat config for the frontend.
//
// Purpose: replace the pre-Track-20.9 fake `lint` stub in package.json
// with a real ESLint gate that catches genuine runtime bugs
// (undefined identifiers, empty catches, unstable nested components,
// hooks violations, dead JSX props, etc.).
//
// The rule set intentionally MIRRORS the platform's existing static-
// lint tool (see /opt/plugins-venv/.../linters/frontend/eslint.config.js)
// so `yarn lint` produces the same signal that CI already checks.
//
// react-hooks/exhaustive-deps is intentionally OFF — this codebase uses
// many hand-tuned useEffect dep arrays and enabling it would produce
// hundreds of noisy false positives without changing behavior.
//
// This file is Track 20.9 · Zero-Drift-safe. It does NOT change any
// runtime behavior. It only enforces what CRA has always required.

import globals from "globals";
import reactHooks from "eslint-plugin-react-hooks";
import react from "eslint-plugin-react";

export default [
  // Skip build artifacts, dependencies, and non-source directories.
  {
    ignores: [
      "build/**",
      "node_modules/**",
      "public/**",
      "scripts/**",
      "**/*.min.js",
    ],
  },
  {
    files: ["src/**/*.js", "src/**/*.jsx"],
    languageOptions: {
      ecmaVersion: 2022,
      sourceType: "module",
      parserOptions: {
        ecmaFeatures: { jsx: true },
      },
      globals: {
        ...globals.browser,
        ...globals.node,
        ...globals.jest,
        React: "readonly",
      },
    },
    plugins: {
      react,
      "react-hooks": reactHooks,
    },
    settings: {
      react: { version: "detect" },
    },
    rules: {
      // Critical runtime-bug detectors — errors here indicate real defects.
      "no-undef": "error",
      "no-unreachable": "error",
      "no-dupe-keys": "error",
      "no-dupe-args": "error",
      "no-duplicate-case": "error",
      "no-empty": "error",
      "no-ex-assign": "error",
      "no-func-assign": "error",
      "no-invalid-regexp": "error",
      "no-obj-calls": "error",
      "no-regex-spaces": "error",
      "no-sparse-arrays": "error",
      "use-isnan": "error",
      "valid-typeof": "error",
      // React hooks core rules — v5.2.0 ships these two only.
      "react-hooks/rules-of-hooks": "error",
      "react-hooks/exhaustive-deps": "off",
      // React plugin — catch dead JSX and unstable component patterns.
      "react/jsx-key": "error",
      "react/jsx-no-duplicate-props": "error",
      "react/jsx-no-undef": "error",
      "react/jsx-uses-vars": "error",
      "react/no-children-prop": "error",
      "react/no-danger-with-children": "error",
      "react/no-deprecated": "error",
      "react/no-direct-mutation-state": "error",
      "react/no-string-refs": "error",
      "react/no-unescaped-entities": "error",
      "react/no-unknown-property": "error",
      "react/no-unstable-nested-components": "error",
      "react/void-dom-elements-no-children": "error",
      "react/jsx-no-target-blank": "error",
      "react/jsx-no-script-url": "error",
    },
  },
];
