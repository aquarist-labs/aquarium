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
      icon: 'mdi:apps',
      route: '/dashboard'
    },
    {
      name: TEXT('Hosts'),
      icon: 'mdi:server-network',
      route: '/dashboard/hosts'
    },
    {
      name: TEXT('Services'),
      icon: 'mdi:share-variant',
      route: '/dashboard/services'
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
