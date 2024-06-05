// The image specification options. The ones in quotes are the default, if nothing is specified for that category of specification, it will assume this one.

Image<['eRead' | eWrite | eReadWrite], ['eAccessPoint' | eAccessRanged1D | eAccessRanged2D | eAccessRandom], ['eEdgeNone' | eEdgeClamped | eEdgeConstant]> image;

// For example these two lines produce the same result

Image<> src;
Image<eRead, eAccessPoint, eEdgeNone> src;


// for loop that counts up from 0 to iterations-1. This will loop the same amount of times as 'iterations'.

for(int i = 0; i < iterations; i++){



}

// The same as above, but starting from 1 and ending at iterations. This may be more intuative for you.

for(int i = 1; i <= iterations; i++){



}

// X/Y for loop. Useful for blurs and other box-based iteration

for(int X = 1; X <= resolution.x; X++){
	for(int Y = 1; Y <= resolution.y; Y++){



 }
}

// Function layout

[inline | blank] [datatype] [functionName]([datatype][inputVariable1], [datatype][inputVariable1], etc...) {


	[operations go here]


	return [output with same datatype]

}

// for example

inline float4 multiplyer(float4 image, float mult){

	image = image * mult;


	return image;


}

// matrix transformation function

inline float4 matrixTransform(float4 image, float4x4 matrix){

    float4 matrixTransformsOutput;

    matrixTransformsOutput.x = image.x * matrix[0][0] + image.y * matrix[0][1] + image.z * matrix[0][2] + matrix[0][3];
    matrixTransformsOutput.y = image.x * matrix[1][0] + image.y * matrix[1][1] + image.z * matrix[1][2] + matrix[1][3];
    matrixTransformsOutput.z = image.x * matrix[2][0] + image.y * matrix[2][1] + image.z * matrix[2][2] + matrix[2][3];
    matrixTransformsOutput.w = image.x * matrix[3][0] + image.y * matrix[3][1] + image.z * matrix[3][2] + matrix[3][3];


    return matrixTransformsOutput;

}

// matrix to screenspace function

inline float4 matrixToScreenspace(float4 image, float focal, float haperture, float vaperture, int2 resolution){

    image.x = 0.5f - ((image.x) * (focal/haperture))/image.z;
    image.y = 0.5f - ((image.y) * (focal/vaperture))/image.z;
    image.z = 0.0f;

    image.x = max(0.0f, min(image.x, 1.0f) )*resolution.x;
    image.y = max(0.0f, min(image.y, 1.0f) )*resolution.y;

    return image;


}


//random access bilinear process. This assumes an eAccessPoint dst and an eAccessRandom image

void process(int2 pos){




	dst() = bilinear(imageName, pos.x, pos.y);

}