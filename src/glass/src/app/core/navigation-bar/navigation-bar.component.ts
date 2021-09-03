/*
 * Project Aquarium's frontend (glass)
 * Copyright (C) 2021 SUSE, LLC.
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 */
import { Component, OnInit } from '@angular/core';
import { marker as TEXT } from '@biesbjerg/ngx-translate-extract-marker';

import { NavItem } from '~/app/core/navigation-bar/navigation-bar-item/navigation-bar-item.component';

@Component({
  selector: 'glass-navigation-bar',
  templateUrl: './navigation-bar.component.html',
  styleUrls: ['./navigation-bar.component.scss']
})
export class NavigationBarComponent implements OnInit {
  showSubmenu = false;
  navItems: NavItem[] = [
    {
      name: TEXT('Dashboard'),
      icon: 'mdi mdi-apps',
      route: '/dashboard'
    },
    {
      name: TEXT('Users'),
      icon: 'mdi mdi-account-multiple',
      route: '/dashboard/users'
    },
    {
      name: TEXT('Hosts'),
      icon: 'mdi mdi-server-network',
      route: '/dashboard/hosts'
    }
  ];

  /* Subitem example. Can be removed as soon as we
     have an actual sub-item ;)
     {
       name: 'Parent Item',
       icon: 'mdi:apps',
       children: [{
         name: 'Subitem1',
         icon: 'mdi:airplane',
         route: '/subitem1'
       },{
         name: 'Subitem2',
         icon: 'mdi:account',
          route: '/subitem2'
      }]
    }
   */

  constructor() {}

  ngOnInit(): void {}
}
