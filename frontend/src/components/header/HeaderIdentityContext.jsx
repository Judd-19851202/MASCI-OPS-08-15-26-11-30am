import React from "react";

const defaultValue = {
  headerOwnsWorkflowIdentity: false,
  pageTitle: null,
  portalLabel: null,
  setHeaderIdentity: () => {},
  clearHeaderIdentity: () => {},
};

const HeaderIdentityContext = React.createContext(defaultValue);

export function HeaderIdentityProvider({ value, children }) {
  return (
    <HeaderIdentityContext.Provider value={{ ...defaultValue, ...(value || {}) }}>
      {children}
    </HeaderIdentityContext.Provider>
  );
}

export function useHeaderIdentity() {
  return React.useContext(HeaderIdentityContext);
}

export default HeaderIdentityContext;