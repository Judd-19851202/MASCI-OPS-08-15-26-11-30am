/* eslint-env jest */
/* global jest, describe, test, expect, beforeEach */

import { installPortalXhrAuth } from "@/lib/xhrPortalAuth";

jest.mock("@/lib/authHeaders", () => ({
  buildPortalAuthHeaders: () => ({
    "X-Admin-Token": "admin-token",
    "X-Directory-Token": "directory-token",
  }),
}));

describe("installPortalXhrAuth", () => {
  const originalEnv = process.env.REACT_APP_BACKEND_URL;

  beforeEach(() => {
    delete window.__masciPortalXhrAuthInstalled;
    process.env.REACT_APP_BACKEND_URL = "https://mascidocs.com";
  });

  test("attaches portal + directory headers to API xhr requests", () => {
    const setRequestHeader = jest.fn();
    const open = jest.fn(function open(_method, url) { this.__url = url; });
    const send = jest.fn();

    function FakeXHR() {}
    FakeXHR.prototype.open = open;
    FakeXHR.prototype.send = send;
    FakeXHR.prototype.setRequestHeader = setRequestHeader;

    const originalXHR = window.XMLHttpRequest;
    window.XMLHttpRequest = FakeXHR;

    installPortalXhrAuth();

    const xhr = new window.XMLHttpRequest();
    xhr.open("POST", "/api/admin/upload");
    xhr.send(new FormData());

    expect(setRequestHeader).toHaveBeenCalledWith("X-Admin-Token", "admin-token");
    expect(setRequestHeader).toHaveBeenCalledWith("X-Directory-Token", "directory-token");

    window.XMLHttpRequest = originalXHR;
    process.env.REACT_APP_BACKEND_URL = originalEnv;
  });
});