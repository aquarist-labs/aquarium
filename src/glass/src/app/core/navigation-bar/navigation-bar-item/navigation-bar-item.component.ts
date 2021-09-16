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
import { Component, Input, OnInit } from '@angular/core';
import { Router } from '@angular/router';

export type NavItem = {
  name: string;
  icon: string;
  route?: string;
  children?: NavItem[];
};

@Component({
  selector: 'glass-navigation-bar-item',
  templateUrl: './navigation-bar-item.component.html',
  styleUrls: ['./navigation-bar-item.component.scss']
})
export class NavigationBarItemComponent implements OnInit {
  @Input() item!: NavItem;
  @Input() depth = 0;
  showSub = false;

  constructor(private router: Router) {}

  ngOnInit(): void {}

  itemClicked(item: NavItem) {
    if (!item.children || !item.children.length) {
      this.router.navigate([item.route]);
    } else if (item.children && item.children.length) {
      this.showSub = !this.showSub;
    }
  }
}
