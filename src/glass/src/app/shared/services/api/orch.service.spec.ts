import { HttpClientTestingModule, HttpTestingController } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';

import { OrchService } from './orch.service';

describe('OrchService', () => {
  let service: OrchService;
  let httpTesting: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [HttpClientTestingModule]
    });
    service = TestBed.inject(OrchService);
    httpTesting = TestBed.inject(HttpTestingController);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });

  it('should call devices', () => {
    service.devices().subscribe();
    const req = httpTesting.expectOne('api/orch/devices');
    expect(req.request.method).toBe('GET');
  });

  it('should call hosts', () => {
    service.hosts().subscribe();
    const req = httpTesting.expectOne('api/orch/hosts');
    expect(req.request.method).toBe('GET');
  });

  it('should call assimilateDevices', () => {
    service.assimilateDevices().subscribe();
    const req = httpTesting.expectOne('api/orch/devices/assimilate');
    expect(req.request.method).toBe('POST');
  });

  it('should call assimilateStatus', () => {
    service.assimilateStatus().subscribe();
    const req = httpTesting.expectOne('api/orch/devices/all_assimilated');
    expect(req.request.method).toBe('GET');
  });

  it('should call facts', () => {
    service.facts().subscribe();
    const req = httpTesting.expectOne('api/orch/facts');
    expect(req.request.method).toBe('GET');
  });
});
