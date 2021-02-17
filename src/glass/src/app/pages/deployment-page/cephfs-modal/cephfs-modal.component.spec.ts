import { ComponentFixture, TestBed } from '@angular/core/testing';

import { CephfsModalComponent } from '~/app/pages/deployment-page/cephfs-modal/cephfs-modal.component';

describe('CephfsModalComponent', () => {
  let component: CephfsModalComponent;
  let fixture: ComponentFixture<CephfsModalComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [CephfsModalComponent]
    }).compileComponents();
  });

  beforeEach(() => {
    fixture = TestBed.createComponent(CephfsModalComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
