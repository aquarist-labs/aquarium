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
import { TranslateModule } from '@ngx-translate/core';
import { ToastrModule } from 'ngx-toastr';

import { NetworkFormComponent } from '~/app/pages/network-page/network-form/network-form.component';
import { PagesModule } from '~/app/pages/pages.module';
import { TestingModule } from '~/app/testing.module';

describe('NetworkFormComponent', () => {
  let component: NetworkFormComponent;
  let fixture: ComponentFixture<NetworkFormComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [PagesModule, TestingModule, ToastrModule.forRoot(), TranslateModule.forRoot()]
    }).compileComponents();
  });

  beforeEach(() => {
    fixture = TestBed.createComponent(NetworkFormComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
