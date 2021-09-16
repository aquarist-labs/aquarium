import { ComponentFixture, TestBed } from '@angular/core/testing';
import { NgbActiveModal } from '@ng-bootstrap/ng-bootstrap';
import { TranslateModule } from '@ngx-translate/core';
import { ToastrModule } from 'ngx-toastr';

import { CoreModule } from '~/app/core/core.module';
import { DeclarativeFormModalComponent } from '~/app/core/modals/declarative-form/declarative-form-modal.component';
import { GLASS_DIALOG_DATA } from '~/app/shared/services/dialog.service';

describe('DeclarativeFormModalComponent', () => {
  let component: DeclarativeFormModalComponent;
  let fixture: ComponentFixture<DeclarativeFormModalComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [CoreModule, ToastrModule.forRoot(), TranslateModule.forRoot()],
      providers: [
        { provide: GLASS_DIALOG_DATA, useValue: {} },
        {
          provide: NgbActiveModal,
          useValue: {}
        }
      ]
    }).compileComponents();
  });

  beforeEach(() => {
    fixture = TestBed.createComponent(DeclarativeFormModalComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
