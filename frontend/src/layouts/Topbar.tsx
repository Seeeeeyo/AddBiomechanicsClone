// @flow
import React, { useState } from "react";
import { Link } from "react-router-dom";
import classNames from "classnames";

// components
import LanguageDropdown from "../components/LanguageDropdown";
import ProfileDropdown from "../components/ProfileDropdown";

import logo from "../assets/images/logo-black-sm.svg";
import logoSmall from "../assets/images/logo-black-xs.svg";
import { propTypes } from "react-bootstrap/esm/Image";

type TopbarProps = {
  hideLogo?: boolean;
  isMenuOpened?: boolean;
  openLeftMenuCallBack?: () => void;
  navCssClasses?: string;
};

const Topbar = (props: TopbarProps) => {
  const navbarCssClasses = props.navCssClasses || "";
  const containerCssClasses = !props.hideLogo ? "container-fluid" : "";

  return (
    <>
      <div className={`navbar-custom ${navbarCssClasses}`}>
        <div className={containerCssClasses}>
          {!props.hideLogo && (
            <Link to="/" className="topnav-logo">
              <span className="topnav-logo-lg">
                <img src={logo} alt="logo" height="60" />
              </span>
              <span className="topnav-logo-sm">
                <img src={logoSmall} alt="logo" height="60" />
              </span>
            </Link>
          )}

          <ul className="list-unstyled topbar-menu float-end mb-0">
            {/*
            <li className="dropdown notification-list topbar-dropdown d-none d-lg-block">
              <LanguageDropdown />
            </li>
            */}
            <li className="dropdown notification-list topbar-dropdown d-lg-block">
              <ProfileDropdown />
            </li>
          </ul>

          <Link
            to="#"
            className={classNames("navbar-toggle", {
              open: props.isMenuOpened,
            })}
            onClick={(e) => {
              e.preventDefault();
              if (props.openLeftMenuCallBack) {
                props.openLeftMenuCallBack();
              }
            }}
          >
            <div className="lines">
              <span></span>
              <span></span>
              <span></span>
            </div>
          </Link>
        </div>
      </div>
    </>
  );
};

export default Topbar;