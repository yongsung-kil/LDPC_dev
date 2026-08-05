#include "channel.h"
double r_offset;
double r_offset2;
double r_offset3;
double LLR_th;
double LLR_th2;
double LLR_th3;
//=============================================
// Read offset @@@@
//=============================================
void Set_R_Offset(int init_n)
{
	r_offset = 0;
	r_offset2 = 0;
	r_offset3 = 0;
	if (MODE_DEC_2SD == init_n) {
		r_offset = 0.35;
	}
	else if (MODE_DEC_3SD == init_n) {
		r_offset = 0.15;
		r_offset2 = 0.35;
		r_offset3 = 0.55;
	}
	else if (MODE_DEC_1_5SD == init_n) {
		/* Simulation@@ @@@,@@ erasure region @@@@--> Very weak@@ erasure@@  */
		r_offset = 0.15;
		r_offset2 = -0.15;
	}
}
//=============================================
// AWGN channel model @@@@ LLR @@@
//=============================================
void Set_LLR_Th(double var)
{
	LLR_th = 2 * r_offset / var;
	LLR_th2 = 2 * r_offset2 / var;
	LLR_th3 = 2 * r_offset3 / var;
}
//=============================================
// LLR @@@@ @@@@@@@@ mag @@ 2@@@@@ @j@@@I@G@
//=============================================
void Get_Mag_2SD(double Lq_ini_m, int* sd)
{
	if (Lq_ini_m >= LLR_th)		*sd = 1;
	else				*sd = 0;
}
//=============================================
// LLR @@@@ @@@@@@@@ mag @@ 4@@@@@ @j@@@ @G@
//=============================================
void Get_Mag_3SD(double Lq_ini_m, int* sd, int* cc)
{
	if (Lq_ini_m >= LLR_th3) { *sd = 1; *cc = 1; }
	else if (Lq_ini_m >= LLR_th2) { *sd = 1; *cc = 0; }
	else if (Lq_ini_m >= LLR_th) { *sd = 0; *cc = 0; }
	else { *sd = 0; *cc = 1; }
}
//=============================================
// LLR @@@@ @@@@@@@@ erasure @G@
//=============================================
void Get_Mag_1_5SD(double Lq_ini, int* hd, int* sd)
{
	// 1st read
	if (Lq_ini >= LLR_th)	*hd = 0;
	else			*hd = 1;
	// 2nd read
	if (Lq_ini <= LLR_th2)	*sd = 1;
	else			*sd = 0;
}
//=============================================
// @E'@@@ RBER@@ @@@@@@@@ AWGN@@@@@@@@ SNR @@@
//=============================================
double SNR_from_RBER(double p)
{
	double u;
	u = pow(qfunc_inv(p), 2) / 2;
	return u;
}
//=============================================
// @E'@@@ RBER@@ @@@@@@@@ N(0,var)
// distribution@@ variance @@@
//=============================================
double dev_from_RBER(double p)
{
	double SNR, var, dev;
	SNR = SNR_from_RBER(p);
	var = 1 / (2 * SNR);
	dev = sqrt(var);
	return dev;
}
//=============================================
// Q function
//=============================================
double Q_fn(double arg)
{
	const double p = 0.2316419, b[5] = { 0.3198153, -0.356563782,
		1.781477937, -1.821255978, 1.330274429 };
	double t, q_fn, temp_t = 1, temp_q = 0;
	t = 1 / (1 + p * arg);
	for (int i = 0; i < 5; i++)
	{
		temp_t *= t;
		temp_q += b[i] * temp_t;
	}
	q_fn = exp(-(arg * arg) / 2) / sqrt(2 * M_PI_m) * temp_q;
	return(q_fn);
}
//=============================================
// Inverse Q function
//=============================================
double qfunc_inv(double p)
{
	const double a[6] = {
		-3.969683028665376e+01,  2.209460984245205e+02,
		-2.759285104469687e+02,  1.383577518672690e+02,
		-3.066479806614716e+01,  2.506628277459239e+00
	};
	const double b[5] = {
		-5.447609879822406e+01,  1.615858368580409e+02,
		-1.556989798598866e+02,  6.680131188771972e+01,
		-1.328068155288572e+01
	};
	const double c[6] = {
		-7.784894002430293e-03, -3.223964580411365e-01,
		-2.400758277161838e+00, -2.549732539343734e+00,
		 4.374664141464968e+00,  2.938163982698783e+00
	};
	const double d[4] = {
		 7.784695709041462e-03,  3.224671290700398e-01,
		 2.445134137142996e+00,  3.754408661907416e+00
	};
	double t, u;
	t = sqrt(-2 * log(p));
	u = -(((((c[0] * t + c[1]) * t + c[2]) * t + c[3]) * t + c[4]) * t + c[5])
		/ ((((d[0] * t + d[1]) * t + d[2]) * t + d[3]) * t + 1);
	return u;
}
//=============================================
// error function
//=============================================
double erf_m(double x)
{
	double y = 1.0 / (1.0 + 0.3275911 * x);
	return 1 - (((((
		+1.061405429 * y
		- 1.453152027) * y
		+ 1.421413741) * y
		- 0.284496736) * y
		+ 0.254829592) * y)
		* exp(-x * x);
}
//=============================================
// Complementary error function
//=============================================
double erfc_m(double x)
{
	return 1 - erf_m(x);
}
