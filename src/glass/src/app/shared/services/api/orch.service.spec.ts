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

  it('should call setNtp', () => {
    service.setNtp('test.test.test').subscribe();
    const req = httpTesting.expectOne('api/orch/ntp');
    expect(req.request.method).toBe('PUT');
  });
});
