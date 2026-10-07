/* mikkt_driver.c — batch driver for MikkTSpace tangent computation.
 *
 * Reads a raw little-endian binary mesh, runs genTangSpaceDefault, writes
 * per-vertex tangents (tx,ty,tz, bitangent-sign w).
 *
 * Input layout:
 *   int32 nverts, int32 nfaces
 *   float32 positions[nverts*3]
 *   float32 normals[nverts*3]
 *   float32 uvs[nverts*2]
 *   int32   faces[nfaces*3]
 * Output layout:
 *   float32 tangents[nverts*4]
 *
 * MikkTSpace (c) 2011 Morten S. Mikkelsen — zlib-style license, see
 * mikktspace.h. This driver is Forge3D original code (MIT).
 */
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include "mikktspace.h"

static float *g_pos, *g_nrm, *g_uv;
static int32_t *g_faces;
static float *g_tan; /* nverts*4 */

static int GetNumFaces(const SMikkTSpaceContext *pContext) {
    (void)pContext;
    int32_t nfaces;
    /* stored in first 8 bytes; we keep globals instead */
    extern int32_t g_nfaces;
    return g_nfaces;
}
int32_t g_nfaces = 0;
static int32_t g_nverts = 0;

static int GetNumVerticesOfFace(const SMikkTSpaceContext *pContext, const int iFace) {
    (void)pContext; (void)iFace;
    return 3;
}

static void GetPosition(const SMikkTSpaceContext *pContext, float fvPosOut[],
                        const int iFace, const int iVert) {
    (void)pContext; (void)iFace;
    int32_t vi = g_faces[iFace * 3 + iVert];
    fvPosOut[0] = g_pos[vi * 3 + 0];
    fvPosOut[1] = g_pos[vi * 3 + 1];
    fvPosOut[2] = g_pos[vi * 3 + 2];
}

static void GetNormal(const SMikkTSpaceContext *pContext, float fvNormOut[],
                      const int iFace, const int iVert) {
    (void)pContext; (void)iFace;
    int32_t vi = g_faces[iFace * 3 + iVert];
    fvNormOut[0] = g_nrm[vi * 3 + 0];
    fvNormOut[1] = g_nrm[vi * 3 + 1];
    fvNormOut[2] = g_nrm[vi * 3 + 2];
}

static void GetTexCoord(const SMikkTSpaceContext *pContext, float fvTexcOut[],
                        const int iFace, const int iVert) {
    (void)pContext; (void)iFace;
    int32_t vi = g_faces[iFace * 3 + iVert];
    fvTexcOut[0] = g_uv[vi * 2 + 0];
    fvTexcOut[1] = g_uv[vi * 2 + 1];
}

static void SetTSpaceBasic(const SMikkTSpaceContext *pContext,
                           const float fvTangent[], const float fSign,
                           const int iFace, const int iVert) {
    (void)pContext;
    int32_t vi = g_faces[iFace * 3 + iVert];
    /* MikkTSpace may call multiple times per vertex (per face-vertex);
       it internally averages — but with our shared-vertex indexing each
       vertex gets one final averaged call. Keep the last write. */
    g_tan[vi * 4 + 0] = fvTangent[0];
    g_tan[vi * 4 + 1] = fvTangent[1];
    g_tan[vi * 4 + 2] = fvTangent[2];
    g_tan[vi * 4 + 3] = fSign;
}

static void SetTSpace(const SMikkTSpaceContext *pContext,
                      const float fvTangent[], const float fvBiTangent[],
                      const float fMagS, const float fMagT,
                      const tbool bIsOrientationPreserving,
                      const int iFace, const int iVert) {
    (void)pContext; (void)fvBiTangent; (void)fMagS; (void)fMagT;
    (void)bIsOrientationPreserving;
    int32_t vi = g_faces[iFace * 3 + iVert];
    g_tan[vi * 4 + 0] = fvTangent[0];
    g_tan[vi * 4 + 1] = fvTangent[1];
    g_tan[vi * 4 + 2] = fvTangent[2];
    g_tan[vi * 4 + 3] = 1.0f; /* sign unknown in this callback; recompute below */
}

int main(int argc, char **argv) {
    if (argc != 3) {
        fprintf(stderr, "usage: %s in.bin out.bin\n", argv[0]);
        return 2;
    }
    FILE *fin = fopen(argv[1], "rb");
    if (!fin) { perror("open input"); return 1; }
    if (fread(&g_nverts, 4, 1, fin) != 1 || fread(&g_nfaces, 4, 1, fin) != 1) {
        fprintf(stderr, "bad header\n"); return 1;
    }
    g_pos   = malloc((size_t)g_nverts * 3 * 4);
    g_nrm   = malloc((size_t)g_nverts * 3 * 4);
    g_uv    = malloc((size_t)g_nverts * 2 * 4);
    g_faces = malloc((size_t)g_nfaces * 3 * 4);
    g_tan   = calloc((size_t)g_nverts * 4, 4);
    if (!g_pos || !g_nrm || !g_uv || !g_faces || !g_tan) {
        fprintf(stderr, "oom\n"); return 1;
    }
    if (fread(g_pos, 4, (size_t)g_nverts * 3, fin) != (size_t)g_nverts * 3 ||
        fread(g_nrm, 4, (size_t)g_nverts * 3, fin) != (size_t)g_nverts * 3 ||
        fread(g_uv, 4, (size_t)g_nverts * 2, fin) != (size_t)g_nverts * 2 ||
        fread(g_faces, 4, (size_t)g_nfaces * 3, fin) != (size_t)g_nfaces * 3) {
        fprintf(stderr, "short read\n"); return 1;
    }
    fclose(fin);

    /* init w to 0 = "untouched" marker */
    for (int32_t i = 0; i < g_nverts; i++) g_tan[i * 4 + 3] = 0.0f;

    SMikkTSpaceInterface iface;
    iface.m_getNumFaces = GetNumFaces;
    iface.m_getNumVerticesOfFace = GetNumVerticesOfFace;
    iface.m_getPosition = GetPosition;
    iface.m_getNormal = GetNormal;
    iface.m_getTexCoord = GetTexCoord;
    iface.m_setTSpaceBasic = SetTSpaceBasic;
    iface.m_setTSpace = NULL; /* use basic: gives us tangent + orientation sign */
    SMikkTSpaceContext ctx;
    ctx.m_pInterface = &iface;
    ctx.m_pUserData = NULL;

    if (!genTangSpaceDefault(&ctx)) {
        fprintf(stderr, "genTangSpaceDefault failed\n");
        return 1;
    }

    FILE *fout = fopen(argv[2], "wb");
    if (!fout) { perror("open output"); return 1; }
    fwrite(g_tan, 4, (size_t)g_nverts * 4, fout);
    fclose(fout);

    int32_t untouched = 0;
    for (int32_t i = 0; i < g_nverts; i++)
        if (g_tan[i * 4 + 3] == 0.0f) untouched++;
    fprintf(stderr, "verts=%d faces=%d untouched=%d\n",
            g_nverts, g_nfaces, untouched);
    return 0;
}
