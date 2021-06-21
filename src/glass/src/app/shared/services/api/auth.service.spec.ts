import { HttpClientTestingModule, HttpTestingController } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';

import { AuthService } from './auth.service';

describe('AuthService', () => {
  let service: AuthService;
  let httpTesting: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [HttpClientTestingModule]
    });
    service = TestBed.inject(AuthService);
    httpTesting = TestBed.inject(HttpTestingController);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });

  it('should call login', () => {
    service.login('test', '01234').subscribe();
    const req = httpTesting.expectOne('api/auth/login');
    expect(req.request.method).toBe('POST');
  });

  it('should call logout', () => {
    service.logout().subscribe();
    const req = httpTesting.expectOne('api/auth/logout');
    expect(req.request.method).toBe('POST');
  });
});
