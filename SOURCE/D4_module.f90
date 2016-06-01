MODULE D4_MODULE
!
! VERSION OF 02/29/2016
!
  INTEGER,SAVE :: IBR_MAX(2)
  INTEGER,SAVE :: NUM_TOP,NUM_BOTTOM,NUM_TOTAL,MAX_BAND
  LOGICAL,SAVE :: FIRST_RUN = .TRUE.
!
! COEFFICIENT ARRAYS
!
  REAL(8),ALLOCATABLE,SAVE :: CC(:),TT(:,:)
!
! WORK ARRAYS
!
  REAL(8),ALLOCATABLE,SAVE :: UPPER_D4(:),ROW(:)
!
! INDEXING ARRAYS
!
  INTEGER,ALLOCATABLE,SAVE :: LINK_D4(:,:)
  INTEGER,ALLOCATABLE,SAVE :: INAT(:),INO(:)
  INTEGER,ALLOCATABLE,SAVE :: IBASE_UPPER(:)
!
  CONTAINS
!
    SUBROUTINE ALLOCATE_COEF(NUM_BLK)
    IMPLICIT NONE
    INTEGER :: NUM_BLK
    !
    FIRST_RUN = .FALSE.
    ALLOCATE (CC(NUM_BLK),TT(NUM_BLK,4))
    !
    RETURN
    END SUBROUTINE
!
!
!
    SUBROUTINE DEALLOCATE_COEF
    IMPLICIT NONE
    !
    FIRST_RUN = .TRUE.
    DEALLOCATE (CC,TT,UPPER_D4,ROW,LINK_D4,INAT,IBASE_UPPER)
    !
    RETURN
    END SUBROUTINE
!
END MODULE