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
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { Router } from '@angular/router';
import { TranslateModule } from '@ngx-translate/core';

import { CoreModule } from '~/app/core/core.module';
import {
  NavigationBarItemComponent,
  NavItem
} from '~/app/core/navigation-bar/navigation-bar-item/navigation-bar-item.component';
import { TestingModule } from '~/app/testing.module';

describe('NavigationBarItemComponent', () => {
  let component: NavigationBarItemComponent;
  let fixture: ComponentFixture<NavigationBarItemComponent>;
  let router: Router;

  const item: NavItem = {
    name: 'item',
    icon: 'mdi:apps',
    route: '/itemroute'
  };
  const itemSubs: NavItem = {
    name: 'itemSubs',
    icon: 'mdi:apps',
    children: [item]
  };

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [CoreModule, TestingModule, TranslateModule.forRoot()]
    }).compileComponents();
  });

  beforeEach(() => {
    fixture = TestBed.createComponent(NavigationBarItemComponent);
    component = fixture.componentInstance;
    component.item = item;
    router = TestBed.inject(Router);
    jest.spyOn(router, 'navigate').mockImplementation();
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should have depth 0 by default', () => {
    expect(component.depth).toBe(0);
  });

  it('should navigate if no children defined', () => {
    component.itemClicked(item);
    expect(router.navigate).toHaveBeenCalledWith(['/itemroute']);
  });

  it('shouldn\'t navigate and show subs if defined', () => {
    component.itemClicked(itemSubs);
    expect(router.navigate).not.toHaveBeenCalled();
    expect(component.showSub).toBe(true);
  });
});
