import { HttpClientTestingModule, HttpTestingController } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';

import { CephfsService } from '~/app/shared/services/api/cephfs.service';

describe('CephfsService', () => {
  let service: CephfsService;
  let httpTesting: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [HttpClientTestingModule]
    });
    service = TestBed.inject(CephfsService);
    httpTesting = TestBed.inject(HttpTestingController);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });

  it('should call authorization', () => {
    service.authorization('foo').subscribe();
    const req = httpTesting.expectOne('api/services/cephfs/auth/foo');
    expect(req.request.method).toBe('GET');
  });
});
