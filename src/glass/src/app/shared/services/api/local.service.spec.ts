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
import { HttpTestingController } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';

import { LocalNodeService } from '~/app/shared/services/api/local.service';
import { TestingModule } from '~/app/testing.module';

describe('LocalNodeService', () => {
  let service: LocalNodeService;
  let httpTesting: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [TestingModule]
    });
    service = TestBed.inject(LocalNodeService);
    httpTesting = TestBed.inject(HttpTestingController);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });

  it('should call local node status', () => {
    service.status().subscribe();
    const req = httpTesting.expectOne('api/local/status');
    expect(req.request.method).toBe('GET');
  });

  it('should get local inventory', () => {
    service.inventory().subscribe();
    const req = httpTesting.expectOne('api/local/inventory');
    expect(req.request.method).toBe('GET');
  });

  it('should get local events', () => {
    service.events().subscribe();
    const req = httpTesting.expectOne('api/local/events');
    expect(req.request.method).toBe('GET');
  });
});
