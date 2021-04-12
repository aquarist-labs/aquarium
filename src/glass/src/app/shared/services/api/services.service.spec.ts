import { HttpClientTestingModule, HttpTestingController } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';

import { ServicesService } from '~/app/shared/services/api/services.service';

describe('ServicesService', () => {
  let service: ServicesService;
  let httpTesting: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [HttpClientTestingModule]
    });
    service = TestBed.inject(ServicesService);
    httpTesting = TestBed.inject(HttpTestingController);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });

  it('should call list', () => {
    service.list().subscribe();
    const req = httpTesting.expectOne('api/services/');
    expect(req.request.method).toBe('GET');
  });

  it('should call stats', () => {
    service.stats().subscribe();
    const req = httpTesting.expectOne('api/services/stats');
    expect(req.request.method).toBe('GET');
  });

  it('should call exists', () => {
    service.exists('foo').subscribe();
    const req = httpTesting.expectOne('api/services/get/foo');
    expect(req.request.method).toBe('GET');
  });
});
