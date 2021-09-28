import { HttpClientTestingModule, HttpTestingController } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';

import { UsersService } from '~/app/shared/services/api/users.service';

describe('UsersService', () => {
  let service: UsersService;
  let httpTesting: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [HttpClientTestingModule]
    });
    service = TestBed.inject(UsersService);
    httpTesting = TestBed.inject(HttpTestingController);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });

  it('should call list', () => {
    service.list().subscribe();
    const req = httpTesting.expectOne('api/users/');
    expect(req.request.method).toBe('GET');
  });

  it('should call create', () => {
    /* eslint-disable @typescript-eslint/naming-convention */
    service
      .create({
        username: 'foo',
        password: 'test123',
        full_name: 'foo bar',
        disabled: true
      })
      .subscribe();
    const req = httpTesting.expectOne('api/users/create');
    expect(req.request.method).toBe('POST');
  });

  it('should call delete', () => {
    service.delete('foo').subscribe();
    const req = httpTesting.expectOne('api/users/foo');
    expect(req.request.method).toBe('DELETE');
  });

  it('should call update', () => {
    service.update('foo', { full_name: 'baz' }).subscribe();
    const req = httpTesting.expectOne('api/users/foo');
    expect(req.request.method).toBe('PATCH');
  });
});
