import { HttpClientTestingModule, HttpTestingController } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';

import { BootstrapService } from './bootstrap.service';

describe('BootstrapService', () => {
  let service: BootstrapService;
  let httpTesting: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [HttpClientTestingModule]
    });
    service = TestBed.inject(BootstrapService);
    httpTesting = TestBed.inject(HttpTestingController);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });

  it('should call start', () => {
    service.start().subscribe();
    const req = httpTesting.expectOne('nodes/deployment/start');
    expect(req.request.method).toBe('POST');
  });

  it('should call status', () => {
    service.status().subscribe();
    const req = httpTesting.expectOne('nodes/deployment/status');
    expect(req.request.method).toBe('GET');
  });
});
