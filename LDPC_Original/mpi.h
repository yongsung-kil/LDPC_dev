#ifndef ECCTG_MPI_H
#define ECCTG_MPI_H

////////////////////////////////////////////////////////////////////
//                   ONLY FOR COMPILE IN WINDOWS                  //
//                   REMOVE FOR SUPERCOM                          //
////////////////////////////////////////////////////////////////////

#define MPI_COMM_WORLD          0
#define MPI_INT                 0
#define MPI_DOUBLE              1
#define MPI_SUM                 0

void MPI_Init(int* argc, char*** argv);
void MPI_Comm_size(int communicator, int* size);
void MPI_Comm_rank(int communicator, int* rank);
void MPI_Finalize();
void MPI_Reduce(int * src, int * dest, int size, int type, int op, int dest_id, int communicator);
void MPI_Reduce(double * src, double * dest, int size, int type, int op, int dest_id, int communicator);
void MPI_Barrier(int communicator);
void MPI_Bcast(int * src, int size, int type, int root, int communicator);
void MPI_Bcast(double * src, int size, int type, int root, int communicator);
#endif
